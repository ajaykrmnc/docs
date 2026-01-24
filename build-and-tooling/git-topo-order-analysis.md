# Git `--topo-order` Performance Analysis

## Overview

The `--topo-order` flag in `git log` causes significant performance issues on large repositories like the Linux kernel.

## What is `--topo-order`?

Topological ordering ensures that:
- **Parent commits always appear before their children** in the output
- Commits are grouped by branch structure rather than chronological order
- The commit graph is displayed in a way that makes branch/merge history clearer

### Ordering Options Comparison

| Option | Description | Performance |
|--------|-------------|-------------|
| `--topo-order` | Parents before children, grouped by branch | **Slowest** - requires full graph traversal |
| `--date-order` | Chronological by commit date | Fast |
| `--author-date-order` | Chronological by author date | Fast |
| (none) | Default ordering | **Fastest** |

## Why is `--topo-order` Slow?

1. **Full Graph Traversal Required**: Git must walk the entire commit DAG (Directed Acyclic Graph) to establish topological order
2. **`--max-count` Doesn't Help**: Even with `-n 10`, git must compute the full order first
3. **Large Repositories Suffer Most**: Linux kernel has ~900,000 commits

## Benchmark Results (Linux 5.4 Repository)

```
Command                                          | Time
-------------------------------------------------|--------
git log --oneline -n 10                          | 0.01s
git log --oneline -n 10 --topo-order             | 4.95s
git log --oneline -n 10 --topo-order (w/ graph)  | 0.04s
```

**Key Finding**: `--topo-order` is ~500x slower without commit-graph cache!

## Solutions

### Solution 1: Generate Commit-Graph (Recommended)

Run once per repository:
```bash
git commit-graph write --reachable
```

Enable automatic maintenance:
```bash
git config --global fetch.writeCommitGraph true
git config --global gc.writeCommitGraph true
```

**Result**: 4.95s → 0.04s (~130x speedup)

### Solution 2: Disable `--topo-order` in Neogit

In your Neovim config, set `commit_order = ""`:

```lua
require('neogit').setup({
  commit_order = "",  -- Disable topo-order for faster loading
})
```

## When is `--topo-order` Important?

**Use topo-order when:**
- Viewing complex merge histories
- Understanding branch relationships
- Generating visual commit graphs

**Skip topo-order when:**
- Working with very large repositories
- Only need recent commits
- Performance is critical

## Neogit Configuration Options

```lua
-- Value passed to the `--<commit_order>-order` flag of `git log`
-- Options:
--   "topo"         topological order (slower on large repos)
--   "date"         chronological by commit date
--   "author-date"  chronological by author date
--   ""             disable explicit ordering (fastest)
commit_order = "topo",  -- default
```

## Recommendation for Linux Kernel Development

For the Linux kernel repository, use **both** solutions:

1. Generate commit-graph: `git commit-graph write --reachable`
2. Optionally set `commit_order = ""` in Neogit config if still slow

This provides the best balance of performance and functionality.

