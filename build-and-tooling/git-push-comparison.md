# Git Push Commands: Standard Push vs Gerrit Code Review Push

## Executive Summary

This document provides a comprehensive comparison between two commonly used git push commands:

1. **`git push origin master`** — Standard direct push to a remote branch
2. **`git push origin HEAD:refs/for/master`** — Gerrit code review push

Understanding these differences is crucial for developers working with Gerrit-based workflows (common in projects like Android, Chromium, and the Linux kernel).

---

## Table of Contents

1. [Command Breakdown](#command-breakdown)
2. [Standard Git Push](#standard-git-push)
3. [Gerrit Push](#gerrit-push)
4. [Key Differences](#key-differences)
5. [Refspec Syntax Explained](#refspec-syntax-explained)
6. [Gerrit Architecture Deep Dive](#gerrit-architecture-deep-dive)
7. [Common Variations and Options](#common-variations-and-options)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Real-World Scenarios](#real-world-scenarios)

---

## Command Breakdown

### Anatomy of a Git Push Command

```
git push <remote> <refspec>
```

- **`<remote>`**: The name of the remote repository (e.g., `origin`)
- **`<refspec>`**: Specifies which local ref to push and where

### Refspec Format

```
<src>:<dst>
```

- **`<src>`**: Local reference (branch, commit, HEAD)
- **`<dst>`**: Destination reference on the remote

---

## Standard Git Push: `git push origin master`

### What It Does

```bash
git push origin master
```

This command pushes your local `master` branch directly to the remote `origin`'s `master` branch.

### Equivalent Full Refspec

```bash
git push origin master:refs/heads/master
```

### Behavior

| Aspect | Description |
|--------|-------------|
| **Target** | `refs/heads/master` on the remote |
| **Access Control** | Requires direct write access to the branch |
| **Review Process** | None — commits are immediately visible |
| **History** | Commits become part of branch history immediately |
| **Visibility** | Changes are instantly available to all users |

### When This Succeeds

1. You have write permissions to the remote branch
2. Your push is a fast-forward (your commits are ahead of remote)
3. Or you use `--force` to overwrite history (dangerous!)

### When This Fails

```
! [rejected]        master -> master (non-fast-forward)
error: failed to push some refs to 'origin'
```

This happens when the remote has commits you don't have locally.

---

## Gerrit Push: `git push origin HEAD:refs/for/master`

### What It Does

```bash
git push origin HEAD:refs/for/master
```

This command pushes your current commit (HEAD) to Gerrit's **magical refs/for/** namespace, which creates a **code review change** targeting the `master` branch.

### Behavior

| Aspect | Description |
|--------|-------------|
| **Target** | `refs/for/master` (Gerrit virtual namespace) |
| **Access Control** | Requires "Push" permission for code review |
| **Review Process** | Creates a Change for review and approval |
| **History** | Commits are NOT in branch history until merged |
| **Visibility** | Visible in Gerrit UI, not in regular git clone |

### The Magic of `refs/for/`

The `refs/for/` prefix is **not a real Git reference**. It's a virtual namespace that Gerrit intercepts:

1. Git sends the push to `refs/for/master`
2. Gerrit intercepts this before it reaches the repository
3. Gerrit creates a "Change" with a unique Change-Id
4. The commit is stored in `refs/changes/XX/YYYY/Z`
5. The original target (`master`) is recorded as the destination branch

### Change Storage

Gerrit stores your pushed commit in a special reference:

```
refs/changes/34/1234/1
            │   │    └── Patch set number
            │   └─────── Change number
            └─────────── Last two digits of change number
```

---

## Key Differences

### Side-by-Side Comparison

| Feature | `git push origin master` | `git push origin HEAD:refs/for/master` |
|---------|--------------------------|----------------------------------------|
| **Purpose** | Direct integration | Code review |
| **Destination** | `refs/heads/master` | Gerrit change queue |
| **Immediate Effect** | Branch updated | Change created for review |
| **Reversibility** | Requires force push | Change can be abandoned |
| **Collaboration** | Limited | Full review workflow |
| **CI Integration** | Post-push only | Pre-merge verification |
| **History Visibility** | Immediate | Only after merge |
| **Typical Use** | Small projects, hotfixes | Enterprise, open source |

### Visual Workflow Comparison

#### Standard Push Workflow

```
Developer                    Remote Repository
    │                              │
    │  git push origin master      │
    │ ────────────────────────────>│
    │                              │
    │                         [Commits added to master]
    │                              │
    │                         [Available to everyone]
    │                              │
```

#### Gerrit Push Workflow

```
Developer                 Gerrit Server              Remote Repository
    │                          │                            │
    │  git push origin         │                            │
    │  HEAD:refs/for/master    │                            │
    │ ────────────────────────>│                            │
    │                          │                            │
    │                    [Change Created]                   │
    │                    [Stored in refs/changes/...]       │
    │                          │                            │
    │                    [Code Review]                      │
    │                    [CI Verification]                  │
    │                          │                            │
    │                    [Approved & Verified]              │
    │                          │                            │
    │                          │ [Submit/Merge]             │
    │                          │───────────────────────────>│
    │                          │                            │
    │                          │                [Now in master]
```

---

## Refspec Syntax Explained

### Understanding HEAD

`HEAD` is a symbolic reference pointing to your current commit:

```bash
# These are equivalent when on master branch:
git push origin master
git push origin HEAD        # If HEAD points to master

# But HEAD is useful when on a feature branch:
git push origin HEAD:refs/for/master    # Push current branch to master review
```

### Refspec Components

```
HEAD:refs/for/master
│    │        │
│    │        └── Target branch for the change
│    └─────────── Gerrit's virtual namespace
└──────────────── Source (current commit)
```

### Common Refspec Patterns

| Refspec | Meaning |
|---------|---------|
| `master` | Push master to origin/master |
| `master:master` | Explicit: push master to master |
| `HEAD:master` | Push current commit to master |
| `HEAD:refs/for/master` | Create Gerrit change for master |
| `HEAD:refs/for/master%topic=fix-bug` | Gerrit change with topic |
| `:master` | Delete remote master branch |

---

## Gerrit Architecture Deep Dive

### How Gerrit Intercepts Pushes

1. **Git Protocol Interception**
   - Gerrit acts as a Git server
   - Intercepts all `refs/for/*` and `refs/drafts/*` pushes
   - Normal pushes to `refs/heads/*` can be allowed or blocked

2. **Change-Id Generation**
   - Each commit should have a unique `Change-Id` in the commit message
   - Format: `Change-Id: I<40 hex characters>`
   - Generated by Gerrit's commit-msg hook

3. **Patch Sets**
   - Each push to the same Change-Id creates a new "patch set"
   - All patch sets are preserved for history

### The Change-Id

```
commit a1b2c3d4...
Author: Developer <dev@example.com>
Date:   Mon Jan 1 12:00:00 2024 +0000

    Add new feature

    This commit adds a new feature that does X, Y, and Z.

    Change-Id: Ie4c8d3f2a1b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9
```

### Why Change-Id is Critical

The Change-Id serves multiple purposes:

1. **Identity**: Uniquely identifies a logical change across patch sets
2. **Tracking**: Allows Gerrit to track iterations of the same change
3. **Rebasing**: Change remains the same even after rebase
4. **Cross-Repository**: Can be used to link related changes

### Installing the Commit-Msg Hook

```bash
# Download the hook from your Gerrit server
scp -p -P 29418 <user>@<gerrit-server>:hooks/commit-msg .git/hooks/

# Or via HTTP
curl -Lo .git/hooks/commit-msg http://<gerrit-server>/tools/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

### Gerrit Reference Namespaces

| Namespace | Purpose |
|-----------|---------|
| `refs/for/<branch>` | Submit change for review to branch |
| `refs/drafts/<branch>` | Submit private draft (deprecated in newer Gerrit) |
| `refs/heads/<branch>` | Direct push (if permitted) |
| `refs/changes/XX/YYYY/Z` | Where changes are actually stored |
| `refs/meta/config` | Project configuration |

### The refs/changes Structure

```
refs/changes/34/1234/1
             │   │   │
             │   │   └── Patch set 1 (first upload)
             │   └────── Change ID 1234
             └────────── Last 2 digits of Change ID (sharding)

refs/changes/34/1234/2   ← Patch set 2 (after amend + push)
refs/changes/34/1234/3   ← Patch set 3 (another iteration)
```

---

## Common Variations and Options

### Gerrit Push Options

```bash
# Push with a topic (groups related changes)
git push origin HEAD:refs/for/master%topic=my-feature

# Push as Work-In-Progress (WIP)
git push origin HEAD:refs/for/master%wip

# Push and mark ready for review
git push origin HEAD:refs/for/master%ready

# Push with specific reviewers
git push origin HEAD:refs/for/master%r=reviewer@example.com

# Push with CC (carbon copy)
git push origin HEAD:refs/for/master%cc=other@example.com

# Combine multiple options
git push origin HEAD:refs/for/master%topic=bugfix,r=alice@example.com,r=bob@example.com

# Push with a commit message for the patch set
git push origin HEAD:refs/for/master%m=Fixed_review_comments

# Push and set a hashtag
git push origin HEAD:refs/for/master%hashtag=urgent

# Push and add a label vote
git push origin HEAD:refs/for/master%l=Code-Review+1

# Push to create a private change
git push origin HEAD:refs/for/master%private

# Remove private flag
git push origin HEAD:refs/for/master%remove-private
```

### Standard Push Options

```bash
# Force push (dangerous - rewrites history)
git push --force origin master

# Force with lease (safer - fails if remote changed)
git push --force-with-lease origin master

# Push all branches
git push --all origin

# Push tags
git push --tags origin

# Dry run (show what would happen)
git push --dry-run origin master

# Set upstream tracking
git push -u origin master

# Delete a remote branch
git push origin --delete feature-branch

# Push with verbosity
git push -v origin master
```

### Push Configuration

```bash
# Set default push behavior
git config push.default current    # Push current branch to same name
git config push.default simple     # Push current to upstream (default)
git config push.default matching   # Push all matching branches

# Configure Gerrit remote
git remote add gerrit ssh://user@gerrit.example.com:29418/project
git config remote.gerrit.push HEAD:refs/for/master
```

---

## Best Practices

### For Standard Git Push

1. **Always Pull Before Push**
   ```bash
   git pull --rebase origin master
   git push origin master
   ```

2. **Avoid Force Push on Shared Branches**
   - Never force push to `master`, `main`, or `develop`
   - If needed, use `--force-with-lease`

3. **Use Branch Protection**
   - Enable branch protection rules
   - Require pull request reviews
   - Require status checks to pass

### For Gerrit Push

1. **Always Install the Commit-Msg Hook**
   ```bash
   gitdir=$(git rev-parse --git-dir)
   scp -p -P 29418 user@gerrit:hooks/commit-msg ${gitdir}/hooks/
   ```

2. **Write Meaningful Commit Messages**
   ```
   Component: Short summary (50 chars or less)

   Detailed explanation of the change. Wrap at 72 characters.
   Explain WHAT changed and WHY, not HOW.

   Bug: 12345
   Change-Id: I1234567890abcdef...
   Signed-off-by: Your Name <email@example.com>
   ```

3. **Keep Changes Small and Focused**
   - One logical change per commit
   - Easier to review
   - Easier to revert if needed

4. **Rebase, Don't Merge**
   ```bash
   git fetch origin
   git rebase origin/master
   git push origin HEAD:refs/for/master
   ```

5. **Amend for Updates**
   ```bash
   # Make changes to files
   git add -u
   git commit --amend
   git push origin HEAD:refs/for/master
   ```

### Gerrit Workflow Tips

1. **Use Topics for Related Changes**
   ```bash
   git push origin HEAD:refs/for/master%topic=feature-x
   ```

2. **Mark Work-In-Progress Early**
   ```bash
   git push origin HEAD:refs/for/master%wip
   ```

3. **Add Reviewers in Push Command**
   ```bash
   git push origin HEAD:refs/for/master%r=alice,r=bob
   ```

---

## Troubleshooting

### Common Standard Push Errors

#### Non-Fast-Forward Rejection

```
! [rejected]        master -> master (non-fast-forward)
```

**Cause**: Remote has commits you don't have

**Solution**:
```bash
git fetch origin
git rebase origin/master
# Resolve any conflicts
git push origin master
```

#### Permission Denied

```
remote: Permission to user/repo.git denied
```

**Cause**: No write access to repository

**Solution**: Check your SSH key or access permissions

### Common Gerrit Push Errors

#### Missing Change-Id

```
remote: ERROR: missing Change-Id in commit message footer
```

**Cause**: Commit doesn't have a Change-Id

**Solution**:
```bash
# Install the hook first
gitdir=$(git rev-parse --git-dir)
scp -p -P 29418 user@gerrit:hooks/commit-msg ${gitdir}/hooks/

# Amend the commit to add Change-Id
git commit --amend --no-edit
git push origin HEAD:refs/for/master
```

#### Change Closed

```
remote: ERROR: change is closed
```

**Cause**: The change was already merged or abandoned

**Solution**: Create a new change with a new Change-Id
```bash
git commit --amend
# Remove the old Change-Id from commit message
# A new one will be generated
git push origin HEAD:refs/for/master
```

#### No New Changes

```
remote: ERROR: no new changes
```

**Cause**: Exact same commit already exists as a patch set

**Solution**: Make a modification or amend the commit
```bash
git commit --amend --no-edit
git push origin HEAD:refs/for/master
```

#### Branch Not Found

```
remote: ERROR: branch refs/heads/feature not found
```

**Cause**: Target branch doesn't exist

**Solution**: Verify the branch name or create it first

#### Permission Denied for refs/for

```
remote: ERROR: Permission denied (create)
```

**Cause**: No permission to create changes

**Solution**: Contact Gerrit administrator for access

---

## Real-World Scenarios

### Scenario 1: Contributing to Android Open Source Project (AOSP)

AOSP uses Gerrit exclusively. Direct pushes are not allowed.

```bash
# 1. Clone the repository
repo init -u https://android.googlesource.com/platform/manifest
repo sync

# 2. Start a new branch
repo start my-feature .

# 3. Make changes and commit
git add .
git commit -m "Fix: Resolve memory leak in ActivityManager

Bug: 123456789
Change-Id: I0123456789abcdef..."

# 4. Upload for review
repo upload .
# Or manually:
git push aosp HEAD:refs/for/master
```

### Scenario 2: Submitting a Patch to a Feature Branch

```bash
# Push to review targeting a feature branch instead of master
git push origin HEAD:refs/for/feature/new-api

# With additional options
git push origin HEAD:refs/for/feature/new-api%topic=api-improvements,r=lead@company.com
```

### Scenario 3: Updating an Existing Change

After receiving review feedback:

```bash
# Make requested changes
vim src/main.c

# Stage changes
git add src/main.c

# Amend the commit (keeps the same Change-Id)
git commit --amend

# Push again - Gerrit creates a new patch set
git push origin HEAD:refs/for/master
```

### Scenario 4: Pushing a Chain of Dependent Changes

```bash
# Create multiple commits
git commit -m "Change 1: Add base infrastructure"
git commit -m "Change 2: Add feature using infrastructure"
git commit -m "Change 3: Add tests for feature"

# Push all at once - Gerrit creates linked changes
git push origin HEAD:refs/for/master

# Each commit becomes a separate change with dependencies
```

### Scenario 5: Linux Kernel Development

The Linux kernel community uses email-based review, but some downstream kernels use Gerrit:

```bash
# Downstream Gerrit-based kernel development
git push origin HEAD:refs/for/kernel-5.4%topic=driver-fix,r=maintainer@company.com

# Standard upstream submission (email-based)
git format-patch -1
git send-email --to=linux-kernel@vger.kernel.org 0001-*.patch
```

### Scenario 6: Cherry-Picking to Multiple Branches

```bash
# Original change on master
git push origin HEAD:refs/for/master%topic=critical-fix

# After approval, cherry-pick to release branches
git checkout release-1.0
git cherry-pick <commit-hash>
git push origin HEAD:refs/for/release-1.0%topic=critical-fix

git checkout release-2.0
git cherry-pick <commit-hash>
git push origin HEAD:refs/for/release-2.0%topic=critical-fix
```

---

## Configuration Examples

### .gitconfig for Gerrit Workflow

```ini
[alias]
    # Push to Gerrit for review
    review = push origin HEAD:refs/for/master

    # Push to Gerrit with topic
    review-topic = "!f() { git push origin HEAD:refs/for/master%topic=$1; }; f"

    # Push as WIP
    wip = push origin HEAD:refs/for/master%wip

    # Amend and push
    amend-review = "!git commit --amend && git push origin HEAD:refs/for/master"

[remote "origin"]
    url = ssh://user@gerrit.example.com:29418/project
    fetch = +refs/heads/*:refs/remotes/origin/*
    # Optional: default push to Gerrit
    push = HEAD:refs/for/master

[push]
    default = nothing  # Prevent accidental pushes
```

### .git/hooks/pre-push for Safety

```bash
#!/bin/bash
# Prevent direct pushes to master

protected_branch='master'
current_branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')

if [ "$current_branch" = "$protected_branch" ]; then
    remote="$1"
    url="$2"

    while read local_ref local_sha remote_ref remote_sha; do
        if [[ "$remote_ref" == "refs/heads/master" ]]; then
            echo "ERROR: Direct push to master is not allowed!"
            echo "Use: git push origin HEAD:refs/for/master"
            exit 1
        fi
    done
fi

exit 0
```

---

## Quick Reference Card

### Standard Push Commands

| Command | Description |
|---------|-------------|
| `git push` | Push current branch to upstream |
| `git push origin master` | Push master to origin/master |
| `git push -u origin branch` | Push and set upstream |
| `git push --force` | Force push (dangerous!) |
| `git push --force-with-lease` | Safe force push |
| `git push origin :branch` | Delete remote branch |

### Gerrit Push Commands

| Command | Description |
|---------|-------------|
| `git push origin HEAD:refs/for/master` | Basic Gerrit push |
| `...%topic=name` | Add topic |
| `...%wip` | Mark as Work-In-Progress |
| `...%ready` | Mark as ready for review |
| `...%r=email` | Add reviewer |
| `...%cc=email` | Add CC |
| `...%l=Label+1` | Add label vote |
| `...%private` | Make change private |
| `...%hashtag=tag` | Add hashtag |

---

## Conclusion

Understanding the difference between `git push origin master` and `git push origin HEAD:refs/for/master` is fundamental for developers working in different environments:

- **Use `git push origin master`** for small projects, personal repositories, or when you have direct commit access and don't need code review.

- **Use `git push origin HEAD:refs/for/master`** when working with Gerrit, which enforces code review before integration. This is standard in large organizations and open-source projects like AOSP, Chromium, and many enterprise environments.

The key insight is that Gerrit's `refs/for/` namespace is a virtual construct that transforms a simple push into a sophisticated code review workflow, providing:

- Pre-merge verification
- Collaborative review
- Traceability
- Quality gates
- Historical record of all iterations

Choose the right approach based on your project's requirements and governance model.

---

*Document created: February 2026*
*Last updated: February 11, 2026*

