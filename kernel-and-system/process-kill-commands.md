# Process Management: Finding and Killing Processes

## The Problem
You have a process (like a Node.js server) running on port 8002 and need to stop it.

---

## Step 1: Find the Process → `lsof -i :PORT`

```bash
lsof -i :8002
```

**What it does:** Lists open files/sockets on port 8002.

**Output:**
```
COMMAND   PID       USER   FD   TYPE  DEVICE SIZE/OFF NODE NAME
node    67059 ajay.kumar  212u  IPv4  ...    0t0  TCP localhost:teradataordbms (LISTEN)
```

**Key info:** PID `67059` is the process ID you need to kill.

---

## Step 2: Kill the Process

### Option A: `kill PID` (Graceful - SIGTERM)
```bash
kill 67059
```

- Sends **SIGTERM** (signal 15) - a "please terminate" request
- Process **can intercept** this signal and perform cleanup (close files, save state, close connections)
- **Preferred method** - gives process a chance to exit cleanly

### Option B: `kill -9 PID` (Forceful - SIGKILL)
```bash
kill -9 67059
```

- Sends **SIGKILL** (signal 9) - immediate termination by the OS
- Process **cannot intercept** or ignore this signal
- **Use when:** `kill` alone doesn't work (process is hung/unresponsive)
- **Downside:** No cleanup - may leave temp files, corrupt data, or orphan child processes

---

## Quick Reference: Common Signals

| Signal | Number | Name | Behavior |
|--------|--------|------|----------|
| SIGTERM | 15 | Terminate | Graceful shutdown (default for `kill`) |
| SIGKILL | 9 | Kill | Forced termination (cannot be caught) |
| SIGINT | 2 | Interrupt | Same as pressing Ctrl+C |
| SIGHUP | 1 | Hangup | Often used to reload config |
| SIGSTOP | 19 | Stop | Pause process (cannot be caught) |

---

## Alternative: `pkill` (Kill by Name)

Instead of finding PID first, kill by process name:

```bash
pkill node          # Graceful kill all 'node' processes
pkill -9 node       # Force kill all 'node' processes
pkill -f "server.js" # Kill by full command match
```

**Caution:** `pkill node` kills ALL node processes, not just the one on port 8002!

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────┐
│  1. Find process on port                                │
│     lsof -i :8002                                       │
│                          ↓                              │
│  2. Try graceful kill first                             │
│     kill 67059                                          │
│                          ↓                              │
│  3. If still running, force kill                        │
│     kill -9 67059                                       │
│                          ↓                              │
│  4. Verify it's gone                                    │
│     lsof -i :8002   (should return empty)               │
└─────────────────────────────────────────────────────────┘
```

---

## Why SIGTERM Before SIGKILL?

| SIGTERM (kill) | SIGKILL (kill -9) |
|----------------|-------------------|
| ✅ Closes database connections properly | ❌ Connections may hang |
| ✅ Saves pending data | ❌ Data may be lost |
| ✅ Removes temp/lock files | ❌ Orphan files remain |
| ✅ Notifies child processes | ❌ Zombies may occur |

**Rule of thumb:** Always try `kill` first, use `kill -9` only when necessary.

