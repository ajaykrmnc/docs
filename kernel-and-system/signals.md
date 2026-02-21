# Unix Signals

## A Comprehensive Study of Software Interrupts and Process Notification

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Signal fundamentals, handling, generation, advanced concepts, and real-time signals

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Signal Fundamentals](#2-signal-fundamentals)
3. [Signal Generation](#3-signal-generation)
4. [Signal Handling](#4-signal-handling)
5. [Signal Sets and Blocking](#5-signal-sets-and-blocking)
6. [Advanced Signal Handling](#6-advanced-signal-handling)
7. [Real-Time Signals](#7-real-time-signals)
8. [Signals and Threads](#8-signals-and-threads)
9. [Signal Safety and Best Practices](#9-signal-safety-and-best-practices)
10. [Modern Alternatives](#10-modern-alternatives)
11. [Summary and Reference](#11-summary-and-reference)

---

## 1. Introduction

### What are Signals?

Signals are software interrupts delivered to a process to notify it of events. They are one of the oldest IPC mechanisms in Unix, providing asynchronous notification of various conditions.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNALS: SOFTWARE INTERRUPTS                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A signal is an asynchronous notification sent to a process or thread    │
│   to notify it of an event that occurred:                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ANALOGY: Signals are like tapping someone on the shoulder         │ │
│   │                                                                     │ │
│   │   👤 Process executing normally...                                  │ │
│   │   👆 TAP! (signal arrives)                                          │ │
│   │   🔄 Process stops, handles the interruption                        │ │
│   │   👤 Process resumes (or terminates, depending on signal)           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY CHARACTERISTICS:                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│   • ASYNCHRONOUS: Can arrive at any time                                  │
│   • LIGHTWEIGHT: Carry minimal information (just the signal number)       │
│   • LIMITED: Only ~31 standard signals (64 with real-time signals)        │
│   • INTERRUPTIVE: Normal execution is suspended                           │
│                                                                            │
│   SIGNAL SOURCES:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌──────────────┐                                                  │ │
│   │   │    KERNEL    │───► Hardware exceptions (SIGFPE, SIGSEGV)        │ │
│   │   │              │───► Software conditions (SIGPIPE, SIGCHLD)       │ │
│   │   └──────────────┘                                                  │ │
│   │          │                                                          │ │
│   │          │   ┌────────────┐         ┌─────────────────┐             │ │
│   │          └──►│  PROCESS   │────────►│ TARGET PROCESS  │             │ │
│   │              │  (sender)  │         │   (receiver)    │             │ │
│   │              │            │  kill() │                 │             │ │
│   │              └────────────┘         └─────────────────┘             │ │
│   │                                                                     │ │
│   │   ┌──────────────┐                                                  │ │
│   │   │   TERMINAL   │───► Ctrl+C (SIGINT), Ctrl+Z (SIGTSTP)           │ │
│   │   │  (keyboard)  │───► Ctrl+\ (SIGQUIT)                            │ │
│   │   └──────────────┘                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION OF UNIX SIGNALS                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1970s - EARLY UNIX (V7)                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Basic signal() function introduced                                    │
│   • Unreliable signals: handler reset to default after each signal        │
│   • Race conditions between signal delivery and handler installation      │
│   • Limited signal set                                                    │
│                                                                            │
│   1980s - BSD AND SYSTEM V DIVERGENCE                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│   • BSD introduced reliable signals with sigvec()                         │
│   • System V added sigset(), sighold(), sigrelse()                        │
│   • Incompatible implementations caused portability nightmares            │
│                                                                            │
│   1988 - POSIX.1                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│   • sigaction() standardized reliable signal handling                     │
│   • Signal sets (sigset_t) for blocking multiple signals                  │
│   • sigprocmask() for signal mask manipulation                            │
│   • Portable interface finally available                                  │
│                                                                            │
│   1993 - POSIX.1b (Real-Time Extensions)                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Real-time signals (SIGRTMIN to SIGRTMAX)                              │
│   • Queued signals with sigqueue()                                        │
│   • Payload data (sigval) can accompany signals                           │
│                                                                            │
│   2000s - MODERN LINUX                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│   • signalfd() for synchronous signal handling                            │
│   • Better thread support with pthread_kill(), pthread_sigqueue()         │
│   • Improved signal semantics for multi-threaded programs                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Signals vs Hardware Interrupts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNALS VS HARDWARE INTERRUPTS                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Signals are sometimes called "software interrupts" because they share   │
│   conceptual similarities with hardware interrupts:                        │
│                                                                            │
│   ┌─────────────────────────────┬─────────────────────────────────────┐   │
│   │    HARDWARE INTERRUPTS      │         SOFTWARE SIGNALS             │   │
│   ├─────────────────────────────┼─────────────────────────────────────┤   │
│   │ Generated by hardware       │ Generated by kernel or processes    │   │
│   │ Handled in kernel mode      │ Handled in user mode (mostly)       │   │
│   │ CPU stops current instruc.  │ Process stops at next opportunity   │   │
│   │ Uses Interrupt Vector Table │ Uses signal handler table           │   │
│   │ Immediate response          │ Deferred until safe point           │   │
│   │ Cannot be blocked (NMI)     │ Most can be blocked                 │   │
│   │ Low-level hardware events   │ High-level software events          │   │
│   └─────────────────────────────┴─────────────────────────────────────┘   │
│                                                                            │
│   WHEN IS A SIGNAL ACTUALLY DELIVERED?                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Signal is "posted" immediately but "delivered" at:               │ │
│   │                                                                     │ │
│   │   • Return from system call                                         │ │
│   │   • Return from interrupt handler                                   │ │
│   │   • When process is scheduled to run                                │ │
│   │   • At certain "safe points" in kernel                              │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │ Process in                Signal      Process                │   │ │
│   │   │ User Mode ──► Syscall ──► Posted ──► Returns ──► Delivered   │   │ │
│   │   │                   │                      │            │       │   │ │
│   │   │                   ▼                      ▼            ▼       │   │ │
│   │   │              Kernel Mode            User Mode     Handler     │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Signal Fundamentals

### Standard Signals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    STANDARD UNIX SIGNALS                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   POSIX defines a standard set of signals. Here are the most important:   │
│                                                                            │
│   TERMINATION SIGNALS:                                                     │
│   ┌────────┬─────────┬───────────────────────────────────────────────────┐│
│   │ Signal │ Number  │ Description                                       ││
│   ├────────┼─────────┼───────────────────────────────────────────────────┤│
│   │ SIGHUP │   1     │ Hangup - terminal disconnected                    ││
│   │ SIGINT │   2     │ Interrupt - Ctrl+C pressed                        ││
│   │ SIGQUIT│   3     │ Quit - Ctrl+\ pressed (core dump)                 ││
│   │ SIGKILL│   9     │ Kill - cannot be caught or ignored                ││
│   │ SIGTERM│  15     │ Terminate - graceful termination request          ││
│   └────────┴─────────┴───────────────────────────────────────────────────┘│
│                                                                            │
│   ERROR SIGNALS (generated by hardware/kernel):                            │
│   ┌────────┬─────────┬───────────────────────────────────────────────────┐│
│   │ Signal │ Number  │ Description                                       ││
│   ├────────┼─────────┼───────────────────────────────────────────────────┤│
│   │ SIGILL │   4     │ Illegal instruction                               ││
│   │ SIGABRT│   6     │ Abort - from abort() function                     ││
│   │ SIGFPE │   8     │ Floating-point exception (div by zero)            ││
│   │ SIGSEGV│  11     │ Segmentation violation - invalid memory access    ││
│   │ SIGBUS │   7     │ Bus error - misaligned memory access              ││
│   └────────┴─────────┴───────────────────────────────────────────────────┘│
│                                                                            │
│   JOB CONTROL SIGNALS:                                                     │
│   ┌────────┬─────────┬───────────────────────────────────────────────────┐│
│   │ Signal │ Number  │ Description                                       ││
│   ├────────┼─────────┼───────────────────────────────────────────────────┤│
│   │ SIGTSTP│  20     │ Terminal stop - Ctrl+Z pressed                    ││
│   │ SIGSTOP│  19     │ Stop - cannot be caught (like SIGKILL)            ││
│   │ SIGCONT│  18     │ Continue - resume stopped process                 ││
│   │ SIGTTIN│  21     │ Background process tried to read from terminal    ││
│   │ SIGTTOU│  22     │ Background process tried to write to terminal     ││
│   └────────┴─────────┴───────────────────────────────────────────────────┘│
│                                                                            │
│   NOTIFICATION SIGNALS:                                                    │
│   ┌────────┬─────────┬───────────────────────────────────────────────────┐│
│   │ Signal │ Number  │ Description                                       ││
│   ├────────┼─────────┼───────────────────────────────────────────────────┤│
│   │ SIGCHLD│  17     │ Child status changed (terminated/stopped)         ││
│   │ SIGPIPE│  13     │ Write to pipe with no readers                     ││
│   │ SIGALRM│  14     │ Alarm clock - timer expired                       ││
│   │ SIGUSR1│  10     │ User-defined signal 1                             ││
│   │ SIGUSR2│  12     │ User-defined signal 2                             ││
│   │ SIGURG │  23     │ Urgent data on socket                             ││
│   │ SIGIO  │  29     │ I/O possible (async I/O)                          ││
│   └────────┴─────────┴───────────────────────────────────────────────────┘│
│                                                                            │
│   NOTE: Signal numbers vary between Unix variants! Use symbolic names.    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Default Signal Actions

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEFAULT SIGNAL DISPOSITIONS                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Each signal has a default action if not handled:                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   TERM (Terminate)      - Process terminates                        │ │
│   │   ─────────────────────────────────────────────────────────────     │ │
│   │   SIGHUP, SIGINT, SIGKILL, SIGPIPE, SIGALRM, SIGTERM,              │ │
│   │   SIGUSR1, SIGUSR2, SIGPOLL, SIGPROF, SIGVTALRM                    │ │
│   │                                                                     │ │
│   │   CORE (Terminate + Core Dump)                                      │ │
│   │   ─────────────────────────────────────────────────────────────     │ │
│   │   SIGQUIT, SIGILL, SIGABRT, SIGFPE, SIGSEGV, SIGBUS,               │ │
│   │   SIGSYS, SIGTRAP, SIGXCPU, SIGXFSZ                                │ │
│   │                                                                     │ │
│   │   STOP (Stop Process)                                               │ │
│   │   ─────────────────────────────────────────────────────────────     │ │
│   │   SIGSTOP, SIGTSTP, SIGTTIN, SIGTTOU                               │ │
│   │                                                                     │ │
│   │   CONT (Continue if Stopped)                                        │ │
│   │   ─────────────────────────────────────────────────────────────     │ │
│   │   SIGCONT                                                           │ │
│   │                                                                     │ │
│   │   IGN (Ignore)                                                      │ │
│   │   ─────────────────────────────────────────────────────────────     │ │
│   │   SIGCHLD, SIGURG, SIGWINCH                                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   UNCATCHABLE SIGNALS:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Two signals CANNOT be caught, blocked, or ignored:                │ │
│   │                                                                     │ │
│   │   • SIGKILL (9)  - Always terminates the process                   │ │
│   │   • SIGSTOP (19) - Always stops the process                        │ │
│   │                                                                     │ │
│   │   This ensures the system can always control runaway processes.    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Signal Lifecycle

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL LIFECYCLE                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A signal goes through several states:                                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌───────────┐      ┌───────────┐      ┌───────────┐              │ │
│   │   │ GENERATED │─────►│  PENDING  │─────►│ DELIVERED │              │ │
│   │   └───────────┘      └───────────┘      └───────────┘              │ │
│   │         │                  │                  │                     │ │
│   │         │                  │                  │                     │ │
│   │         ▼                  ▼                  ▼                     │ │
│   │   Signal is sent     Signal waiting      Handler executes          │ │
│   │   to process         for delivery        or default action         │ │
│   │                      (may be blocked)                               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DETAILED STATE TRANSITIONS:                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. GENERATION                                                     │ │
│   │      • Kernel or another process calls kill()                       │ │
│   │      • Hardware exception occurs                                    │ │
│   │      • User presses Ctrl+C                                          │ │
│   │                                                                     │ │
│   │   2. PENDING STATE                                                  │ │
│   │      • Signal is recorded in process's pending signal set           │ │
│   │      • For standard signals: only ONE instance kept (no queuing)    │ │
│   │      • For real-time signals: multiple instances queued             │ │
│   │                                                                     │ │
│   │   3. BLOCKED (optional)                                             │ │
│   │      • If signal is in process's signal mask, remains pending       │ │
│   │      • Will be delivered when unblocked                             │ │
│   │                                                                     │ │
│   │   4. DELIVERY                                                       │ │
│   │      • Signal is removed from pending set                           │ │
│   │      • Disposition checked: handler, default, or ignore             │ │
│   │      • Handler executes (if installed)                              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL DATA STRUCTURES:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct task_struct {                                              │ │
│   │       ...                                                           │ │
│   │       struct signal_struct *signal;    /* Shared signal state */   │ │
│   │       struct sighand_struct *sighand;  /* Signal handlers */       │ │
│   │       sigset_t blocked;                /* Blocked signals */       │ │
│   │       sigset_t pending;                /* Pending signals */       │ │
│   │       ...                                                           │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   struct sighand_struct {                                           │ │
│   │       spinlock_t siglock;                                          │ │
│   │       struct k_sigaction action[_NSIG];  /* Handler array */       │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Signal Generation

### The kill() System Call

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SENDING SIGNALS: kill()                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int kill(pid_t pid, int sig);                                           │
│                                                                            │
│   Returns: 0 on success, -1 on error                                      │
│                                                                            │
│                                                                            │
│   ARGUMENTS:                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   pid > 0     Signal sent to process with that PID                 │ │
│   │   pid == 0    Signal sent to all processes in sender's group       │ │
│   │   pid == -1   Signal sent to all processes (with permission)       │ │
│   │   pid < -1    Signal sent to process group |pid|                   │ │
│   │                                                                     │ │
│   │   sig == 0    No signal sent, but error checking performed         │ │
│   │               (useful to check if process exists)                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLES:                                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   // Send SIGTERM to process 1234                                         │
│   kill(1234, SIGTERM);                                                    │
│                                                                            │
│   // Send SIGINT to own process group                                     │
│   kill(0, SIGINT);                                                        │
│                                                                            │
│   // Check if process exists                                              │
│   if (kill(pid, 0) == -1 && errno == ESRCH) {                            │
│       printf("Process %d does not exist\n", pid);                        │
│   }                                                                       │
│                                                                            │
│   // Send signal to process group 500                                     │
│   kill(-500, SIGHUP);                                                     │
│                                                                            │
│                                                                            │
│   PERMISSIONS:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   To send a signal, one of these must be true:                     │ │
│   │                                                                     │ │
│   │   • Sender is privileged (CAP_KILL capability)                     │ │
│   │   • Sender's real or effective UID matches receiver's real or     │ │
│   │     saved set-user-ID                                               │ │
│   │   • SIGCONT can be sent to any process in same session            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### raise() and Related Functions

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    OTHER SIGNAL GENERATION FUNCTIONS                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   RAISE: Send signal to self                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int raise(int sig);                                                     │
│                                                                            │
│   Equivalent to: kill(getpid(), sig);  // in single-threaded             │
│   Equivalent to: pthread_kill(pthread_self(), sig);  // in multi-thread  │
│                                                                            │
│                                                                            │
│   KILLPG: Send signal to process group                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int killpg(pid_t pgrp, int sig);                                        │
│                                                                            │
│   Equivalent to: kill(-pgrp, sig);                                        │
│                                                                            │
│                                                                            │
│   ABORT: Send SIGABRT to self                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void abort(void);                                                       │
│                                                                            │
│   • Sends SIGABRT to calling process                                      │
│   • Cannot return - either handler terminates or default action           │
│   • Results in core dump (if enabled)                                     │
│                                                                            │
│                                                                            │
│   ALARM: Schedule SIGALRM delivery                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   unsigned int alarm(unsigned int seconds);                               │
│                                                                            │
│   • Schedules SIGALRM to be delivered after 'seconds' seconds            │
│   • Returns seconds remaining from previous alarm (0 if none)            │
│   • alarm(0) cancels any pending alarm                                    │
│   • Only one alarm can be pending at a time                               │
│                                                                            │
│   // Example: Timeout for an operation                                    │
│   alarm(5);  // SIGALRM in 5 seconds                                     │
│   result = slow_operation();                                              │
│   alarm(0);  // Cancel if operation completed                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 4. Signal Handling

### The signal() Function (Legacy)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LEGACY SIGNAL HANDLING: signal()                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   typedef void (*sighandler_t)(int);                                       │
│   sighandler_t signal(int signum, sighandler_t handler);                  │
│                                                                            │
│   Returns: Previous handler on success, SIG_ERR on error                  │
│                                                                            │
│                                                                            │
│   HANDLER VALUES:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SIG_DFL     - Restore default action                             │ │
│   │   SIG_IGN     - Ignore the signal                                  │ │
│   │   &handler    - Custom handler function                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void sigint_handler(int sig) {                                          │
│       printf("Caught SIGINT!\n");                                         │
│   }                                                                       │
│                                                                            │
│   int main() {                                                            │
│       signal(SIGINT, sigint_handler);  // Install handler                 │
│       signal(SIGTERM, SIG_IGN);        // Ignore SIGTERM                  │
│       signal(SIGHUP, SIG_DFL);         // Default for SIGHUP              │
│       // ...                                                              │
│   }                                                                       │
│                                                                            │
│                                                                            │
│   ⚠️  PROBLEMS WITH signal():                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. UNRELIABLE (on some systems):                                  │ │
│   │      • Handler reset to SIG_DFL after each signal                   │ │
│   │      • Race condition: signal can arrive before re-installation     │ │
│   │                                                                     │ │
│   │   2. NON-PORTABLE BEHAVIOR:                                         │ │
│   │      • Different behavior on BSD vs System V                        │ │
│   │      • System calls may or may not restart                          │ │
│   │                                                                     │ │
│   │   3. LIMITED CONTROL:                                               │ │
│   │      • Cannot block signals during handler                          │ │
│   │      • Cannot retrieve additional signal information                │ │
│   │                                                                     │ │
│   │   RECOMMENDATION: Use sigaction() for new code                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The sigaction() Function (Modern)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RELIABLE SIGNAL HANDLING: sigaction()                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int sigaction(int signum, const struct sigaction *act,                  │
│                 struct sigaction *oldact);                                │
│                                                                            │
│   Returns: 0 on success, -1 on error                                      │
│                                                                            │
│                                                                            │
│   THE SIGACTION STRUCTURE:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct sigaction {                                                │ │
│   │       void     (*sa_handler)(int);           /* Simple handler */   │ │
│   │       void     (*sa_sigaction)(int, siginfo_t *, void *);          │ │
│   │                                              /* Extended handler */ │ │
│   │       sigset_t   sa_mask;     /* Signals blocked during handler */  │ │
│   │       int        sa_flags;    /* Behavior modifiers */              │ │
│   │       void     (*sa_restorer)(void);         /* Not used */        │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IMPORTANT FLAGS:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SA_SIGINFO     Use sa_sigaction instead of sa_handler            │ │
│   │                  Provides additional info via siginfo_t             │ │
│   │                                                                     │ │
│   │   SA_RESTART     Automatically restart interrupted system calls    │ │
│   │                  (read, write, etc.)                                │ │
│   │                                                                     │ │
│   │   SA_NOCLDSTOP   Don't receive SIGCHLD when children stop          │ │
│   │                                                                     │ │
│   │   SA_NOCLDWAIT   Don't create zombie children                      │ │
│   │                                                                     │ │
│   │   SA_NODEFER     Don't block signal while handler runs             │ │
│   │                                                                     │ │
│   │   SA_RESETHAND   Reset to SIG_DFL after handler (like signal())    │ │
│   │                                                                     │ │
│   │   SA_ONSTACK     Use alternate signal stack (set by sigaltstack)   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void handler(int sig) {                                                 │
│       write(STDOUT_FILENO, "Signal caught\n", 14);                       │
│   }                                                                       │
│                                                                            │
│   int main() {                                                            │
│       struct sigaction sa;                                                │
│                                                                            │
│       sa.sa_handler = handler;                                            │
│       sigemptyset(&sa.sa_mask);                                           │
│       sigaddset(&sa.sa_mask, SIGQUIT);  /* Block SIGQUIT in handler */   │
│       sa.sa_flags = SA_RESTART;                                           │
│                                                                            │
│       if (sigaction(SIGINT, &sa, NULL) == -1) {                          │
│           perror("sigaction");                                            │
│           exit(1);                                                        │
│       }                                                                   │
│                                                                            │
│       /* ... */                                                           │
│   }                                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 5. Signal Sets and Blocking

### Signal Set Manipulation

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL SETS: sigset_t                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A signal set is a data structure representing a collection of signals.  │
│   Used for blocking signals, checking pending signals, etc.               │
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   INITIALIZATION FUNCTIONS:                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int sigemptyset(sigset_t *set);                                  │ │
│   │       Initialize set to empty (no signals)                         │ │
│   │                                                                     │ │
│   │   int sigfillset(sigset_t *set);                                   │ │
│   │       Initialize set to full (all signals)                         │ │
│   │                                                                     │ │
│   │   Both return: 0 on success, -1 on error                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MANIPULATION FUNCTIONS:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int sigaddset(sigset_t *set, int signum);                        │ │
│   │       Add signal to set                                            │ │
│   │                                                                     │ │
│   │   int sigdelset(sigset_t *set, int signum);                        │ │
│   │       Remove signal from set                                       │ │
│   │                                                                     │ │
│   │   int sigismember(const sigset_t *set, int signum);                │ │
│   │       Test if signal is in set                                     │ │
│   │       Returns: 1 if member, 0 if not, -1 on error                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   sigset_t set;                                                           │
│                                                                            │
│   sigemptyset(&set);           // Start with empty set                    │
│   sigaddset(&set, SIGINT);     // Add SIGINT                              │
│   sigaddset(&set, SIGTERM);    // Add SIGTERM                             │
│                                                                            │
│   if (sigismember(&set, SIGINT)) {                                        │
│       printf("SIGINT is in the set\n");                                   │
│   }                                                                       │
│                                                                            │
│   sigdelset(&set, SIGINT);     // Remove SIGINT                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Blocking Signals with sigprocmask()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL BLOCKING: sigprocmask()                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int sigprocmask(int how, const sigset_t *set, sigset_t *oldset);        │
│                                                                            │
│   Returns: 0 on success, -1 on error                                      │
│                                                                            │
│                                                                            │
│   HOW PARAMETER:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SIG_BLOCK     Add signals in 'set' to current mask               │ │
│   │                 new_mask = current_mask | set                       │ │
│   │                                                                     │ │
│   │   SIG_UNBLOCK   Remove signals in 'set' from current mask          │ │
│   │                 new_mask = current_mask & ~set                      │ │
│   │                                                                     │ │
│   │   SIG_SETMASK   Replace current mask with 'set'                    │ │
│   │                 new_mask = set                                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   VISUAL REPRESENTATION:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Signal Mask (blocked signals):                                   │ │
│   │   ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐               │ │
│   │   │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │...│30 │31 │32 │               │ │
│   │   └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘               │ │
│   │     │   │   │                                                       │ │
│   │     0   1   0   (0=unblocked, 1=blocked)                           │ │
│   │         ▲                                                           │ │
│   │         │                                                           │ │
│   │         SIGINT (2) is blocked                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE: Critical Section Protection                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   sigset_t block_set, old_set;                                            │
│                                                                            │
│   // Block SIGINT and SIGTERM during critical section                     │
│   sigemptyset(&block_set);                                                │
│   sigaddset(&block_set, SIGINT);                                          │
│   sigaddset(&block_set, SIGTERM);                                         │
│                                                                            │
│   sigprocmask(SIG_BLOCK, &block_set, &old_set);  // Save old mask        │
│                                                                            │
│   /* Critical section - signals are blocked */                            │
│   update_shared_data();                                                   │
│                                                                            │
│   sigprocmask(SIG_SETMASK, &old_set, NULL);      // Restore old mask     │
│                                                                            │
│                                                                            │
│   NOTE: SIGKILL and SIGSTOP cannot be blocked!                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Checking Pending Signals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PENDING SIGNALS: sigpending()                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int sigpending(sigset_t *set);                                          │
│                                                                            │
│   Returns: 0 on success, -1 on error                                      │
│                                                                            │
│   Retrieves the set of signals that are pending (generated but blocked). │
│                                                                            │
│                                                                            │
│   PENDING vs BLOCKED:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   BLOCKED signals:  Signals that WILL NOT be delivered             │ │
│   │                     (defined by signal mask)                        │ │
│   │                                                                     │ │
│   │   PENDING signals:  Signals that HAVE BEEN generated               │ │
│   │                     but not yet delivered                           │ │
│   │                     (often because they're blocked)                 │ │
│   │                                                                     │ │
│   │   ┌──────────────────────────────────────────────────────────────┐ │ │
│   │   │                                                              │ │ │
│   │   │   Signal Generated ──► Blocked? ──► Yes ──► PENDING         │ │ │
│   │   │                           │                                  │ │ │
│   │   │                           No                                 │ │ │
│   │   │                           │                                  │ │ │
│   │   │                           ▼                                  │ │ │
│   │   │                       DELIVERED                              │ │ │
│   │   │                                                              │ │ │
│   │   └──────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   sigset_t pending;                                                       │
│                                                                            │
│   sigpending(&pending);                                                   │
│                                                                            │
│   if (sigismember(&pending, SIGINT)) {                                    │
│       printf("SIGINT is pending\n");                                      │
│   }                                                                       │
│                                                                            │
│   // Check all signals                                                    │
│   for (int sig = 1; sig < NSIG; sig++) {                                 │
│       if (sigismember(&pending, sig)) {                                  │
│           printf("Signal %d is pending\n", sig);                         │
│       }                                                                   │
│   }                                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 6. Advanced Signal Handling

### The siginfo_t Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EXTENDED SIGNAL INFORMATION: siginfo_t                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When using SA_SIGINFO flag with sigaction(), the handler receives       │
│   additional information about the signal via siginfo_t structure.        │
│                                                                            │
│   SIGINFO_T STRUCTURE:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   siginfo_t {                                                       │ │
│   │       int      si_signo;    /* Signal number */                    │ │
│   │       int      si_errno;    /* Errno value */                      │ │
│   │       int      si_code;     /* Signal code (see below) */          │ │
│   │       pid_t    si_pid;      /* Sending process ID */               │ │
│   │       uid_t    si_uid;      /* Real user ID of sender */           │ │
│   │       int      si_status;   /* Exit value or signal */             │ │
│   │       void    *si_addr;     /* Memory location (for SIGSEGV) */    │ │
│   │       int      si_band;     /* Band event (for SIGPOLL) */         │ │
│   │       union sigval si_value; /* Signal value (real-time) */        │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SI_CODE VALUES:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SI_USER      Signal sent by kill()                               │ │
│   │   SI_KERNEL    Signal sent by kernel                               │ │
│   │   SI_QUEUE     Signal sent by sigqueue()                           │ │
│   │   SI_TIMER     Timer expiration (POSIX timers)                     │ │
│   │   SI_ASYNCIO   Async I/O completion                                │ │
│   │   SI_MESGQ     Message queue state change                          │ │
│   │                                                                     │ │
│   │   For SIGSEGV:                                                      │ │
│   │   SEGV_MAPERR  Address not mapped                                  │ │
│   │   SEGV_ACCERR  Invalid permissions                                 │ │
│   │                                                                     │ │
│   │   For SIGFPE:                                                       │ │
│   │   FPE_INTDIV   Integer divide by zero                              │ │
│   │   FPE_FLTDIV   Float divide by zero                                │ │
│   │   FPE_FLTOVF   Float overflow                                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE: Handler with siginfo_t                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void handler(int sig, siginfo_t *info, void *ucontext) {                │
│       printf("Signal %d from PID %d\n", sig, info->si_pid);              │
│       printf("Code: %d\n", info->si_code);                                │
│                                                                            │
│       if (sig == SIGSEGV) {                                               │
│           printf("Fault address: %p\n", info->si_addr);                  │
│       }                                                                   │
│   }                                                                       │
│                                                                            │
│   // Setup                                                                │
│   struct sigaction sa;                                                    │
│   sa.sa_sigaction = handler;  // Note: sa_sigaction, not sa_handler      │
│   sa.sa_flags = SA_SIGINFO;                                               │
│   sigemptyset(&sa.sa_mask);                                               │
│   sigaction(SIGSEGV, &sa, NULL);                                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Waiting for Signals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WAITING FOR SIGNALS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PAUSE: Wait for any signal                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <unistd.h>                                                      │
│                                                                            │
│   int pause(void);                                                        │
│                                                                            │
│   • Suspends process until a signal is caught                             │
│   • Always returns -1 with errno set to EINTR                             │
│   • Simple but has race condition issues                                  │
│                                                                            │
│                                                                            │
│   SIGSUSPEND: Atomic unblock and wait                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int sigsuspend(const sigset_t *mask);                                   │
│                                                                            │
│   • Atomically: (1) set signal mask to 'mask' (2) suspend process        │
│   • Original mask restored when sigsuspend returns                        │
│   • Always returns -1 with errno EINTR                                    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   WHY SIGSUSPEND IS NEEDED:                                         │ │
│   │                                                                     │ │
│   │   BROKEN (race condition):        CORRECT (atomic):                 │ │
│   │   ─────────────────────────       ─────────────────                 │ │
│   │                                                                     │ │
│   │   sigprocmask(UNBLOCK);           sigsuspend(&mask);                │ │
│   │   /* Signal can arrive here! */   /* Atomic unblock + wait */       │ │
│   │   pause();                                                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE: Waiting for SIGUSR1                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   volatile sig_atomic_t got_signal = 0;                                   │
│                                                                            │
│   void handler(int sig) { got_signal = 1; }                               │
│                                                                            │
│   int main() {                                                            │
│       sigset_t block, empty;                                              │
│       struct sigaction sa;                                                │
│                                                                            │
│       // Install handler                                                  │
│       sa.sa_handler = handler;                                            │
│       sigemptyset(&sa.sa_mask);                                           │
│       sa.sa_flags = 0;                                                    │
│       sigaction(SIGUSR1, &sa, NULL);                                      │
│                                                                            │
│       // Block SIGUSR1                                                    │
│       sigemptyset(&block);                                                │
│       sigaddset(&block, SIGUSR1);                                         │
│       sigprocmask(SIG_BLOCK, &block, NULL);                               │
│                                                                            │
│       // Prepare empty mask for sigsuspend                                │
│       sigemptyset(&empty);                                                │
│                                                                            │
│       while (!got_signal) {                                               │
│           sigsuspend(&empty);  // Wait with signals unblocked             │
│       }                                                                   │
│                                                                            │
│       printf("Got the signal!\n");                                        │
│   }                                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Synchronous Signal Handling with sigwait()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYNCHRONOUS WAITING: sigwait()                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int sigwait(const sigset_t *set, int *sig);                             │
│                                                                            │
│   Returns: 0 on success, positive error number on error                   │
│                                                                            │
│   • Waits for any signal in 'set' to become pending                       │
│   • Returns the signal number in '*sig'                                   │
│   • The signal is NOT delivered to a handler                              │
│   • Useful for synchronous signal handling                                │
│                                                                            │
│                                                                            │
│   SIGWAIT vs SIGSUSPEND:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sigsuspend():                                                     │ │
│   │   • Delivers signal to handler (asynchronous)                      │ │
│   │   • Handler runs in signal context                                 │ │
│   │   • Must be signal-safe                                            │ │
│   │                                                                     │ │
│   │   sigwait():                                                        │ │
│   │   • Returns signal number (synchronous)                            │ │
│   │   • Processing in normal code context                              │ │
│   │   • No signal-safety restrictions                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE: Dedicated signal handling thread                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void *signal_thread(void *arg) {                                        │
│       sigset_t *set = (sigset_t *)arg;                                   │
│       int sig;                                                            │
│                                                                            │
│       while (1) {                                                         │
│           sigwait(set, &sig);                                            │
│                                                                            │
│           switch (sig) {                                                  │
│           case SIGINT:                                                    │
│               printf("Received SIGINT\n");                               │
│               cleanup_and_exit();                                        │
│               break;                                                     │
│           case SIGHUP:                                                    │
│               printf("Received SIGHUP - reloading config\n");           │
│               reload_config();                                           │
│               break;                                                     │
│           }                                                               │
│       }                                                                   │
│       return NULL;                                                        │
│   }                                                                       │
│                                                                            │
│   // In main: block signals, then create thread                           │
│   sigset_t set;                                                           │
│   sigemptyset(&set);                                                      │
│   sigaddset(&set, SIGINT);                                                │
│   sigaddset(&set, SIGHUP);                                                │
│   pthread_sigmask(SIG_BLOCK, &set, NULL);                                │
│   pthread_create(&tid, NULL, signal_thread, &set);                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 7. Real-Time Signals

### Introduction to Real-Time Signals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME SIGNALS (POSIX.1b)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Real-time signals extend standard signals with additional features      │
│   needed for real-time applications and inter-process communication.     │
│                                                                            │
│   SIGNAL NUMBERS:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Standard signals:    1 to 31                                     │ │
│   │   Real-time signals:   SIGRTMIN to SIGRTMAX                        │ │
│   │                                                                     │ │
│   │   Linux typical:                                                    │ │
│   │   SIGRTMIN = 34                                                    │ │
│   │   SIGRTMAX = 64                                                    │ │
│   │   Total:    31 real-time signals available                         │ │
│   │                                                                     │ │
│   │   Note: Use SIGRTMIN+n, not hardcoded numbers!                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY DIFFERENCES FROM STANDARD SIGNALS:                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌─────────────────────┬─────────────────────┬─────────────────┐  │ │
│   │   │ Feature             │ Standard Signals    │ Real-Time       │  │ │
│   │   ├─────────────────────┼─────────────────────┼─────────────────┤  │ │
│   │   │ Queuing             │ No (coalesced)      │ Yes (queued)    │  │ │
│   │   │ Delivery order      │ Undefined           │ Lowest # first  │  │ │
│   │   │ Payload data        │ No                  │ Yes (sigval)    │  │ │
│   │   │ Number range        │ 1-31 (predefined)   │ User-defined    │  │ │
│   │   │ Multiple pending    │ No                  │ Yes             │  │ │
│   │   └─────────────────────┴─────────────────────┴─────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Sending Real-Time Signals with sigqueue()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SENDING REAL-TIME SIGNALS: sigqueue()                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int sigqueue(pid_t pid, int sig, const union sigval value);             │
│                                                                            │
│   Returns: 0 on success, -1 on error                                      │
│                                                                            │
│                                                                            │
│   THE SIGVAL UNION:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   union sigval {                                                    │ │
│   │       int   sival_int;     /* Integer value */                     │ │
│   │       void *sival_ptr;     /* Pointer value */                     │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   Allows sending additional data with the signal.                  │ │
│   │   Retrieved via siginfo_t->si_value in handler.                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE: Sender                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   union sigval value;                                                     │
│   value.sival_int = 42;                                                   │
│                                                                            │
│   // Send SIGRTMIN to process 1234 with value 42                          │
│   if (sigqueue(1234, SIGRTMIN, value) == -1) {                           │
│       perror("sigqueue");                                                 │
│   }                                                                       │
│                                                                            │
│                                                                            │
│   EXAMPLE: Receiver (handler with SA_SIGINFO)                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void handler(int sig, siginfo_t *info, void *ucontext) {                │
│       printf("Received signal %d\n", sig);                                │
│       printf("From PID: %d\n", info->si_pid);                            │
│       printf("Value: %d\n", info->si_value.sival_int);                   │
│   }                                                                       │
│                                                                            │
│   // Setup                                                                │
│   struct sigaction sa;                                                    │
│   sa.sa_sigaction = handler;                                              │
│   sa.sa_flags = SA_SIGINFO;                                               │
│   sigemptyset(&sa.sa_mask);                                               │
│   sigaction(SIGRTMIN, &sa, NULL);                                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Signal Queuing

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL QUEUING BEHAVIOR                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   STANDARD SIGNALS (NO QUEUING):                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Send SIGINT 3 times while blocked:                               │ │
│   │                                                                     │ │
│   │   ┌─────┐  ┌─────┐  ┌─────┐                                        │ │
│   │   │ INT │  │ INT │  │ INT │  ─────►  Pending: [INT]  (1 delivery) │ │
│   │   └─────┘  └─────┘  └─────┘                                        │ │
│   │                                                                     │ │
│   │   Multiple instances coalesce into one.                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   REAL-TIME SIGNALS (QUEUED):                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Send SIGRTMIN 3 times while blocked:                             │ │
│   │                                                                     │ │
│   │   ┌─────┐  ┌─────┐  ┌─────┐         ┌─────┬─────┬─────┐            │ │
│   │   │ RT0 │  │ RT0 │  │ RT0 │  ─────► │ RT0 │ RT0 │ RT0 │            │ │
│   │   └─────┘  └─────┘  └─────┘         └─────┴─────┴─────┘            │ │
│   │                                      Queue (3 deliveries)          │ │
│   │                                                                     │ │
│   │   Each instance is queued separately.                              │ │
│   │   FIFO order within same signal number.                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DELIVERY ORDER (multiple signal numbers):                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Pending: SIGRTMIN+2, SIGRTMIN, SIGRTMIN+1                        │ │
│   │                                                                     │ │
│   │   Delivery order:                                                   │ │
│   │   1. SIGRTMIN     (lowest number first)                            │ │
│   │   2. SIGRTMIN+1                                                    │ │
│   │   3. SIGRTMIN+2                                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   QUEUE LIMITS:                                                            │
│   • System-wide limit: RLIMIT_SIGPENDING                                  │
│   • Check with: getrlimit(RLIMIT_SIGPENDING, &rlim)                      │
│   • sigqueue() returns EAGAIN if queue full                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 8. Signals and Threads
[](2026-02-18_.md)
### Thread Signal Concepts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNALS IN MULTI-TH EADED PROGRAMS                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   In POSIX threads, signals have complex interactions with threads.       │
│                                                                            │
│   KEY CONCEPTS:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. SIGNAL HANDLERS are process-wide (shared by all threads)      │ │
│   │                                                                     │ │
│   │   2. SIGNAL MASKS are per-thread (each thread has its own)         │ │
│   │                                                                     │ │
│   │   3. PENDING SIGNALS can be:                                       │ │
│   │      • Process-directed (sent to process)                          │ │
│   │      • Thread-directed (sent to specific thread)                   │ │
│   │                                                                     │ │
│   │   4. SYNCHRONOUS signals (SIGSEGV, SIGFPE) go to offending thread  │ │
│   │                                                                     │ │
│   │   5. ASYNCHRONOUS signals (kill, SIGINT) go to any eligible thread │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SIGNAL DELIVERY IN MULTI-THREADED PROCESS:                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                       PROCESS                               │  │ │
│   │   │   ┌───────────────────────────────────────────────────────┐ │  │ │
│   │   │   │ Signal Handlers (shared)                              │ │  │ │
│   │   │   │ SIGINT -> handler1, SIGTERM -> handler2, ...          │ │  │ │
│   │   │   └───────────────────────────────────────────────────────┘ │  │ │
│   │   │                                                             │  │ │
│   │   │   ┌──────────┐  ┌──────────┐  ┌──────────┐                │  │ │
│   │   │   │ Thread 1 │  │ Thread 2 │  │ Thread 3 │                │  │ │
│   │   │   │──────────│  │──────────│  │──────────│                │  │ │
│   │   │   │ mask:    │  │ mask:    │  │ mask:    │                │  │ │
│   │   │   │ [SIGINT] │  │ []       │  │ [SIGINT] │                │  │ │
│   │   │   └──────────┘  └──────────┘  └──────────┘                │  │ │
│   │   │       ↑ blocked    ↑ unblocked   ↑ blocked                │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   If SIGINT sent to process → delivered to Thread 2 only          │ │
│   │   (the only thread with SIGINT unblocked)                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Thread Signal Functions

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THREAD SIGNAL FUNCTIONS                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PTHREAD_SIGMASK: Thread's signal mask                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int pthread_sigmask(int how, const sigset_t *set, sigset_t *oldset);   │
│                                                                            │
│   • Same semantics as sigprocmask() but for threads                       │
│   • Returns 0 on success, error number on failure                         │
│   • 'how' can be SIG_BLOCK, SIG_UNBLOCK, or SIG_SETMASK                  │
│                                                                            │
│   NOTE: sigprocmask() behavior is undefined in multi-threaded programs!  │
│         Always use pthread_sigmask() in threaded code.                    │
│                                                                            │
│                                                                            │
│   PTHREAD_KILL: Send signal to specific thread                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int pthread_kill(pthread_t thread, int sig);                            │
│                                                                            │
│   • Sends signal to specific thread within process                        │
│   • Returns 0 on success, error number on failure                         │
│   • sig=0 can be used to check if thread exists                          │
│                                                                            │
│                                                                            │
│   EXAMPLE: Block signals in all threads except one                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   // In main(), before creating any threads:                              │
│   sigset_t set;                                                           │
│   sigemptyset(&set);                                                      │
│   sigaddset(&set, SIGINT);                                                │
│   sigaddset(&set, SIGTERM);                                               │
│   sigaddset(&set, SIGHUP);                                                │
│                                                                            │
│   // Block signals - inherited by all new threads                         │
│   pthread_sigmask(SIG_BLOCK, &set, NULL);                                │
│                                                                            │
│   // Create worker threads (they inherit blocked signals)                 │
│   pthread_create(&worker1, NULL, worker_func, NULL);                     │
│   pthread_create(&worker2, NULL, worker_func, NULL);                     │
│                                                                            │
│   // Create dedicated signal handling thread                              │
│   pthread_create(&sig_thread, NULL, signal_handler_thread, &set);        │
│                                                                            │
│   // Signal thread unblocks and handles signals                           │
│   void *signal_handler_thread(void *arg) {                               │
│       sigset_t *set = (sigset_t *)arg;                                   │
│       int sig;                                                            │
│                                                                            │
│       while (1) {                                                         │
│           sigwait(set, &sig);                                            │
│           handle_signal(sig);                                             │
│       }                                                                   │
│   }                                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Best Practices for Signals and Threads

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THREADING AND SIGNALS: BEST PRACTICES                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   RECOMMENDED PATTERNS:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   PATTERN 1: Dedicated Signal Thread                               │ │
│   │   ─────────────────────────────────────────────────────────────    │ │
│   │                                                                     │ │
│   │   1. Block all signals in main thread (before creating threads)   │ │
│   │   2. Create worker threads (inherit blocked signals)              │ │
│   │   3. Create one signal handling thread                            │ │
│   │   4. Signal thread uses sigwait() to handle signals              │ │
│   │                                                                     │ │
│   │   Advantages:                                                       │ │
│   │   • Signals handled synchronously                                  │ │
│   │   • No async-signal-safety concerns                                │ │
│   │   • Predictable behavior                                           │ │
│   │                                                                     │ │
│   │                                                                     │ │
│   │   PATTERN 2: Use signalfd() (Linux-specific)                       │ │
│   │   ─────────────────────────────────────────────────────────────    │ │
│   │                                                                     │ │
│   │   1. Block signals                                                 │ │
│   │   2. Create signalfd for those signals                            │ │
│   │   3. Use poll/epoll/select on signalfd                            │ │
│   │                                                                     │ │
│   │   See Section 10 for details.                                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THINGS TO AVOID:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✗ Using signal() in multi-threaded programs                     │ │
│   │   ✗ Using sigprocmask() instead of pthread_sigmask()              │ │
│   │   ✗ Calling thread-unsafe functions from signal handlers          │ │
│   │   ✗ Using signals for inter-thread communication                  │ │
│   │     (use mutexes, condition variables, or semaphores instead)      │ │
│   │   ✗ Assuming which thread will receive a process-directed signal  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 9. Signal Safety and Best Practices

### Async-Signal-Safe Functions

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ASYNC-SIGNAL-SAFE FUNCTIONS                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A signal handler can be invoked at ANY point in program execution.     │
│   Only a limited set of functions are safe to call from signal handlers. │
│                                                                            │
│   POSIX ASYNC-SIGNAL-SAFE FUNCTIONS:                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SYSTEM CALLS (mostly safe):                                       │ │
│   │   _exit, _Exit, abort, accept, access, alarm, bind, cfgetispeed,   │ │
│   │   cfgetospeed, cfsetispeed, cfsetospeed, chdir, chmod, chown,      │ │
│   │   clock_gettime, close, connect, creat, dup, dup2, execle, execve, │ │
│   │   fchmod, fchown, fcntl, fdatasync, fork, fstat, fsync, ftruncate, │ │
│   │   getegid, geteuid, getgid, getgroups, getpgrp, getpid, getppid,   │ │
│   │   getuid, kill, link, listen, lseek, lstat, mkdir, mkfifo, open,   │ │
│   │   pause, pipe, poll, pselect, raise, read, readlink, recv,         │ │
│   │   recvfrom, recvmsg, rename, rmdir, select, sem_post, send,        │ │
│   │   sendmsg, sendto, setgid, setpgid, setsid, setsockopt, setuid,    │ │
│   │   shutdown, sigaction, sigaddset, sigdelset, sigemptyset,          │ │
│   │   sigfillset, sigismember, signal, sigpause, sigpending,           │ │
│   │   sigprocmask, sigqueue, sigset, sigsuspend, sleep, socket,        │ │
│   │   socketpair, stat, symlink, sysconf, tcdrain, tcflow, tcflush,    │ │
│   │   tcgetattr, tcgetpgrp, tcsendbreak, tcsetattr, tcsetpgrp, time,   │ │
│   │   times, umask, uname, unlink, utime, wait, waitpid, write         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   UNSAFE FUNCTIONS (DO NOT USE IN HANDLERS):                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✗ printf(), fprintf(), sprintf() - use write() instead          │ │
│   │   ✗ malloc(), free(), realloc()    - memory allocation            │ │
│   │   ✗ exit()                          - use _exit() or _Exit()       │ │
│   │   ✗ pthread_* functions             - most thread functions        │ │
│   │   ✗ strtok(), strtol()              - use static data             │ │
│   │   ✗ Any function using errno       - errno may be clobbered        │ │
│   │   ✗ Any function using stdio       - FILE buffers not safe         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Safe Signal Handler Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WRITING SAFE SIGNAL HANDLERS                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE VOLATILE SIG_ATOMIC_T TYPE:                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   volatile sig_atomic_t flag = 0;                                  │ │
│   │                                                                     │ │
│   │   • 'volatile': tells compiler not to optimize/cache the value     │ │
│   │   • 'sig_atomic_t': guaranteed atomic read/write                   │ │
│   │   • Can only store integer values (usually small range)           │ │
│   │                                                                     │ │
│   │   This is the ONLY safe way to communicate between handler and    │ │
│   │   main program (besides calling async-signal-safe functions).      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PATTERN 1: Simple Flag                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   volatile sig_atomic_t got_signal = 0;                                   │
│                                                                            │
│   void handler(int sig) {                                                 │
│       got_signal = 1;  // Just set flag                                   │
│   }                                                                       │
│                                                                            │
│   int main() {                                                            │
│       // Install handler...                                               │
│       while (!got_signal) {                                               │
│           do_work();                                                      │
│       }                                                                   │
│       // Handle signal safely in main context                             │
│       cleanup();                                                          │
│   }                                                                       │
│                                                                            │
│                                                                            │
│   PATTERN 2: Self-Pipe Trick                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int pipefd[2];                                                          │
│                                                                            │
│   void handler(int sig) {                                                 │
│       int saved_errno = errno;                                            │
│       write(pipefd[1], &sig, sizeof(sig));  // Async-signal-safe         │
│       errno = saved_errno;                   // Restore errno             │
│   }                                                                       │
│                                                                            │
│   int main() {                                                            │
│       pipe(pipefd);                                                       │
│       // Set pipefd[1] non-blocking                                       │
│       fcntl(pipefd[1], F_SETFL, O_NONBLOCK);                             │
│                                                                            │
│       // Install handler...                                               │
│                                                                            │
│       // Use select/poll on pipefd[0] with other file descriptors        │
│       while (1) {                                                         │
│           int nfds = poll(fds, nfds, -1);                                │
│           if (fds[PIPE_INDEX].revents & POLLIN) {                        │
│               int sig;                                                    │
│               read(pipefd[0], &sig, sizeof(sig));                        │
│               handle_signal(sig);  // Safe context                       │
│           }                                                               │
│       }                                                                   │
│   }                                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Common Pitfalls and Solutions

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL HANDLING PITFALLS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PITFALL 1: Calling Unsafe Functions                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✗ WRONG:                                                          │ │
│   │   void handler(int sig) {                                           │ │
│   │       printf("Got signal %d\n", sig);  // UNSAFE!                   │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   ✓ CORRECT:                                                        │ │
│   │   void handler(int sig) {                                           │ │
│   │       const char msg[] = "Got signal\n";                            │ │
│   │       write(STDERR_FILENO, msg, sizeof(msg) - 1);                   │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PITFALL 2: Not Saving/Restoring errno                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✗ WRONG:                                                          │ │
│   │   void handler(int sig) {                                           │ │
│   │       write(fd, data, len);  // May modify errno                    │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   ✓ CORRECT:                                                        │ │
│   │   void handler(int sig) {                                           │ │
│   │       int saved_errno = errno;                                      │ │
│   │       write(fd, data, len);                                         │ │
│   │       errno = saved_errno;                                          │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PITFALL 3: Reentrant Signal Delivery                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Problem: Same signal arrives while handler is running            │ │
│   │                                                                     │ │
│   │   Solution: Signal is automatically blocked during handler         │ │
│   │   (unless SA_NODEFER is set)                                        │ │
│   │                                                                     │ │
│   │   For different signals: add them to sa_mask                       │ │
│   │                                                                     │ │
│   │   sa.sa_mask: sigaddset(&sa.sa_mask, SIGQUIT);                     │ │
│   │              sigaddset(&sa.sa_mask, SIGTERM);                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PITFALL 4: Interrupted System Calls                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Problem: read(), write(), etc. return EINTR when interrupted     │ │
│   │                                                                     │ │
│   │   Solution 1: Use SA_RESTART flag                                  │ │
│   │   sa.sa_flags = SA_RESTART;                                        │ │
│   │                                                                     │ │
│   │   Solution 2: Retry on EINTR                                       │ │
│   │   while ((n = read(fd, buf, len)) == -1 && errno == EINTR)        │ │
│   │       continue;                                                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 10. Modern Alternatives (Linux-Specific)

### signalfd() - Signal File Descriptor

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNALFD: FILE DESCRIPTOR FOR SIGNALS                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   signalfd() creates a file descriptor that can receive signals.          │
│   This allows signals to be handled via select/poll/epoll.                │
│                                                                            │
│   SYNOPSIS:                                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <sys/signalfd.h>                                               │
│                                                                            │
│   int signalfd(int fd, const sigset_t *mask, int flags);                 │
│                                                                            │
│   Parameters:                                                              │
│   • fd    : -1 to create new fd, or existing signalfd to modify          │
│   • mask  : set of signals to receive via this fd                        │
│   • flags : SFD_NONBLOCK, SFD_CLOEXEC                                    │
│                                                                            │
│   Returns: file descriptor on success, -1 on error                        │
│                                                                            │
│                                                                            │
│   SIGNALFD_SIGINFO STRUCTURE:                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   struct signalfd_siginfo {                                               │
│       uint32_t ssi_signo;    // Signal number                            │
│       int32_t  ssi_errno;    // Error number (unused)                    │
│       int32_t  ssi_code;     // Signal code (like si_code)               │
│       uint32_t ssi_pid;      // Sending process PID                      │
│       uint32_t ssi_uid;      // Sending process UID                      │
│       int32_t  ssi_fd;       // File descriptor (SIGIO)                  │
│       uint32_t ssi_tid;      // Kernel timer ID (POSIX timers)           │
│       uint32_t ssi_band;     // Band event (SIGIO)                       │
│       uint32_t ssi_overrun;  // POSIX timer overrun count                │
│       uint32_t ssi_trapno;   // Trap number                              │
│       int32_t  ssi_status;   // Exit status or signal (SIGCHLD)          │
│       int32_t  ssi_int;      // Integer sent by sigqueue()               │
│       uint64_t ssi_ptr;      // Pointer sent by sigqueue()               │
│       uint64_t ssi_utime;    // User CPU time (SIGCHLD)                  │
│       uint64_t ssi_stime;    // System CPU time (SIGCHLD)                │
│       uint64_t ssi_addr;     // Fault address (SIGSEGV, SIGBUS)          │
│       /* ... other fields ... */                                          │
│   };                                                                      │
│                                                                            │
│                                                                            │
│   EXAMPLE: Using signalfd with epoll                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <sys/signalfd.h>                                               │
│   #include <sys/epoll.h>                                                  │
│   #include <signal.h>                                                     │
│                                                                            │
│   int main() {                                                            │
│       sigset_t mask;                                                      │
│       sigemptyset(&mask);                                                 │
│       sigaddset(&mask, SIGINT);                                           │
│       sigaddset(&mask, SIGTERM);                                          │
│                                                                            │
│       // Block signals so they go to signalfd                             │
│       sigprocmask(SIG_BLOCK, &mask, NULL);                               │
│                                                                            │
│       // Create signalfd                                                  │
│       int sfd = signalfd(-1, &mask, SFD_NONBLOCK | SFD_CLOEXEC);        │
│                                                                            │
│       // Add to epoll                                                     │
│       int epfd = epoll_create1(EPOLL_CLOEXEC);                           │
│       struct epoll_event ev = {.events = EPOLLIN, .data.fd = sfd};       │
│       epoll_ctl(epfd, EPOLL_CTL_ADD, sfd, &ev);                         │
│                                                                            │
│       // Event loop                                                       │
│       struct epoll_event events[10];                                      │
│       while (1) {                                                         │
│           int n = epoll_wait(epfd, events, 10, -1);                      │
│           for (int i = 0; i < n; i++) {                                  │
│               if (events[i].data.fd == sfd) {                            │
│                   struct signalfd_siginfo info;                          │
│                   read(sfd, &info, sizeof(info));                        │
│                   printf("Got signal %d\n", info.ssi_signo);            │
│               }                                                           │
│           }                                                               │
│       }                                                                   │
│   }                                                                       │
│                                                                            │
│   ADVANTAGES:                                                              │
│   • Signals handled synchronously (no async-signal-safety concerns)       │
│   • Can be multiplexed with other I/O using select/poll/epoll            │
│   • Integrates naturally with event-driven architectures                  │
│   • Rich signal information via signalfd_siginfo                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### eventfd() - Event Notification

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVENTFD: LIGHTWEIGHT EVENT NOTIFICATION                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   eventfd() creates a file descriptor for event notification.             │
│   Not for signals directly, but useful as alternative IPC mechanism.      │
│                                                                            │
│   SYNOPSIS:                                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <sys/eventfd.h>                                                │
│                                                                            │
│   int eventfd(unsigned int initval, int flags);                          │
│                                                                            │
│   Parameters:                                                              │
│   • initval : initial counter value                                       │
│   • flags   : EFD_CLOEXEC, EFD_NONBLOCK, EFD_SEMAPHORE                   │
│                                                                            │
│   Returns: file descriptor on success, -1 on error                        │
│                                                                            │
│                                                                            │
│   USAGE:                                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • write(): adds value to counter                                        │
│   • read():  returns counter and resets to 0                             │
│              (or decrements by 1 with EFD_SEMAPHORE)                      │
│   • poll/select: readable when counter > 0                                │
│                                                                            │
│                                                                            │
│   EXAMPLE: Event notification between threads                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int efd = eventfd(0, EFD_NONBLOCK);                                    │
│                                                                            │
│   // Sender thread/signal handler                                         │
│   void notify() {                                                         │
│       uint64_t val = 1;                                                  │
│       write(efd, &val, sizeof(val));                                     │
│   }                                                                       │
│                                                                            │
│   // Receiver in event loop                                               │
│   if (poll_result & POLLIN) {                                            │
│       uint64_t val;                                                      │
│       read(efd, &val, sizeof(val));                                      │
│       printf("Received %lu events\n", val);                              │
│   }                                                                       │
│                                                                            │
│   USE CASES:                                                               │
│   • Lightweight semaphore (with EFD_SEMAPHORE)                            │
│   • Thread notification mechanism                                         │
│   • Event counting in event loops                                         │
│   • Alternative to condition variables for simple cases                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### pidfd and pidfd_send_signal()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PIDFD: MODERN PROCESS FILE DESCRIPTORS                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   pidfd provides a race-free way to refer to processes using              │
│   file descriptors instead of PIDs (which can be recycled).               │
│                                                                            │
│   CREATING PIDFD:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   // Method 1: pidfd_open (Linux 5.3+)                                    │
│   #include <sys/syscall.h>                                                │
│   int pidfd = syscall(SYS_pidfd_open, pid, 0);                           │
│                                                                            │
│   // Method 2: clone3 with CLONE_PIDFD (Linux 5.2+)                       │
│   // Returns pidfd for the new child process                              │
│                                                                            │
│                                                                            │
│   PIDFD_SEND_SIGNAL:                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <sys/syscall.h>                                                │
│   #include <signal.h>                                                     │
│                                                                            │
│   // int pidfd_send_signal(int pidfd, int sig,                           │
│   //                       siginfo_t *info, unsigned int flags);         │
│                                                                            │
│   int ret = syscall(SYS_pidfd_send_signal, pidfd, SIGTERM, NULL, 0);    │
│                                                                            │
│   Parameters:                                                              │
│   • pidfd : file descriptor from pidfd_open or clone3                    │
│   • sig   : signal number to send                                        │
│   • info  : siginfo_t for additional data (or NULL)                      │
│   • flags : must be 0 currently                                          │
│                                                                            │
│                                                                            │
│   ADVANTAGES OVER KILL():                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   TRADITIONAL kill() RACE:                                          │ │
│   │                                                                     │ │
│   │   1. Process A: pid_t target = get_target_pid();                   │ │
│   │   2. Target process exits                                           │ │
│   │   3. New process starts with same PID                               │ │
│   │   4. Process A: kill(target, SIGTERM);  // Wrong process!          │ │
│   │                                                                     │ │
│   │                                                                     │ │
│   │   WITH pidfd:                                                       │ │
│   │                                                                     │ │
│   │   1. Process A: pidfd = pidfd_open(target_pid, 0);                 │ │
│   │   2. Target process exits                                           │ │
│   │   3. New process starts with same PID                               │ │
│   │   4. Process A: pidfd_send_signal(pidfd, SIGTERM, NULL, 0);        │ │
│   │      → Returns error (ESRCH), won't signal wrong process           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   WAITING WITH PIDFD:                                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   // pidfd is pollable - becomes readable when process exits              │
│   struct pollfd pfd = {.fd = pidfd, .events = POLLIN};                   │
│   poll(&pfd, 1, -1);                                                     │
│                                                                            │
│   // Then reap with waitid                                                │
│   siginfo_t info;                                                        │
│   waitid(P_PIDFD, pidfd, &info, WEXITED);                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Comparison: Traditional vs Modern APIs

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL API COMPARISON                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────┬───────────────────┬─────────────────────────────┐   │
│   │   Feature       │   Traditional     │   Modern (Linux)            │   │
│   ├─────────────────┼───────────────────┼─────────────────────────────┤   │
│   │ Signal receipt  │ signal handlers   │ signalfd() + read()         │   │
│   │ Async-safety    │ Very limited      │ Not needed (synchronous)    │   │
│   │ Event loop      │ Self-pipe trick   │ Native select/poll/epoll    │   │
│   │ Signal queuing  │ sigqueue()        │ signalfd (preserves queue)  │   │
│   │ Process signal  │ kill(pid, sig)    │ pidfd_send_signal()         │   │
│   │ Race-free       │ No                │ Yes (with pidfd)            │   │
│   │ Thread safety   │ pthread_sigmask   │ Same, but easier handling   │   │
│   │ Portability     │ POSIX             │ Linux 2.6.22+ / 5.3+        │   │
│   └─────────────────┴───────────────────┴─────────────────────────────┘   │
│                                                                            │
│   WHEN TO USE WHICH:                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Traditional signal handlers:                                             │
│   • Portable code (non-Linux)                                             │
│   • Simple synchronous signals (SIGCHLD with wait)                        │
│   • Legacy code maintenance                                               │
│                                                                            │
│   signalfd():                                                              │
│   • Event-driven servers (epoll-based)                                    │
│   • Complex signal handling logic                                         │
│   • When you need multiple signals in event loop                          │
│                                                                            │
│   pidfd_send_signal():                                                     │
│   • Process managers/supervisors                                          │
│   • When PID reuse race is a concern                                      │
│   • Container runtimes                                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 11. Summary and Reference

### Quick Reference: Signal Functions

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL FUNCTION QUICK REFERENCE                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SIGNAL GENERATION:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Function              │ Description                                 │ │
│   ├───────────────────────┼─────────────────────────────────────────────┤ │
│   │ kill(pid, sig)        │ Send signal to process/group               │ │
│   │ raise(sig)            │ Send signal to self                        │ │
│   │ killpg(pgrp, sig)     │ Send signal to process group               │ │
│   │ abort()               │ Send SIGABRT to self                       │ │
│   │ alarm(seconds)        │ Schedule SIGALRM after delay               │ │
│   │ sigqueue(pid,sig,val) │ Send RT signal with data                   │ │
│   │ pthread_kill(th,sig)  │ Send signal to thread                      │ │
│   └───────────────────────┴─────────────────────────────────────────────┘ │
│                                                                            │
│   SIGNAL HANDLING:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Function              │ Description                                 │ │
│   ├───────────────────────┼─────────────────────────────────────────────┤ │
│   │ signal(sig, handler)  │ Set handler (legacy, avoid)                │ │
│   │ sigaction(sig,act,old)│ Set handler (preferred)                    │ │
│   └───────────────────────┴─────────────────────────────────────────────┘ │
│                                                                            │
│   SIGNAL SET MANIPULATION:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Function              │ Description                                 │ │
│   ├───────────────────────┼─────────────────────────────────────────────┤ │
│   │ sigemptyset(set)      │ Initialize empty set                       │ │
│   │ sigfillset(set)       │ Initialize full set                        │ │
│   │ sigaddset(set, sig)   │ Add signal to set                          │ │
│   │ sigdelset(set, sig)   │ Remove signal from set                     │ │
│   │ sigismember(set, sig) │ Test if signal in set                      │ │
│   └───────────────────────┴─────────────────────────────────────────────┘ │
│                                                                            │
│   SIGNAL BLOCKING:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Function              │ Description                                 │ │
│   ├───────────────────────┼─────────────────────────────────────────────┤ │
│   │ sigprocmask(how,s,o)  │ Examine/change signal mask                 │ │
│   │ pthread_sigmask(...)  │ Thread-safe signal mask                    │ │
│   │ sigpending(set)       │ Get pending signals                        │ │
│   └───────────────────────┴─────────────────────────────────────────────┘ │
│                                                                            │
│   WAITING FOR SIGNALS:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Function              │ Description                                 │ │
│   ├───────────────────────┼─────────────────────────────────────────────┤ │
│   │ pause()               │ Wait for any signal                        │ │
│   │ sigsuspend(mask)      │ Atomically set mask and wait               │ │
│   │ sigwait(set, sig)     │ Synchronously wait for signal              │ │
│   │ sigwaitinfo(set,info) │ Wait with signal info                      │ │
│   │ sigtimedwait(...)     │ Wait with timeout                          │ │
│   └───────────────────────┴─────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Quick Reference: Standard Signals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    STANDARD SIGNALS REFERENCE                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TERMINATION SIGNALS:                                                     │
│   ┌──────────┬────────┬─────────────────────────────────────────────────┐ │
│   │ Signal   │ Default│ Description                                     │ │
│   ├──────────┼────────┼─────────────────────────────────────────────────┤ │
│   │ SIGTERM  │ Term   │ Graceful termination request                   │ │
│   │ SIGKILL  │ Term   │ Forced termination (cannot catch)              │ │
│   │ SIGINT   │ Term   │ Interrupt from keyboard (Ctrl+C)               │ │
│   │ SIGQUIT  │ Core   │ Quit from keyboard (Ctrl+\)                    │ │
│   │ SIGHUP   │ Term   │ Hangup / terminal disconnect                   │ │
│   └──────────┴────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
│   ERROR SIGNALS:                                                           │
│   ┌──────────┬────────┬─────────────────────────────────────────────────┐ │
│   │ Signal   │ Default│ Description                                     │ │
│   ├──────────┼────────┼─────────────────────────────────────────────────┤ │
│   │ SIGSEGV  │ Core   │ Segmentation fault (invalid memory)            │ │
│   │ SIGBUS   │ Core   │ Bus error (memory alignment)                   │ │
│   │ SIGFPE   │ Core   │ Floating-point exception                       │ │
│   │ SIGILL   │ Core   │ Illegal instruction                            │ │
│   │ SIGABRT  │ Core   │ Abort signal from abort()                      │ │
│   │ SIGSYS   │ Core   │ Bad system call                                │ │
│   └──────────┴────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
│   JOB CONTROL SIGNALS:                                                     │
│   ┌──────────┬────────┬─────────────────────────────────────────────────┐ │
│   │ Signal   │ Default│ Description                                     │ │
│   ├──────────┼────────┼─────────────────────────────────────────────────┤ │
│   │ SIGSTOP  │ Stop   │ Stop process (cannot catch)                    │ │
│   │ SIGTSTP  │ Stop   │ Stop from terminal (Ctrl+Z)                    │ │
│   │ SIGCONT  │ Cont   │ Continue stopped process                       │ │
│   │ SIGTTIN  │ Stop   │ Background read from terminal                  │ │
│   │ SIGTTOU  │ Stop   │ Background write to terminal                   │ │
│   └──────────┴────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
│   NOTIFICATION SIGNALS:                                                    │
│   ┌──────────┬────────┬─────────────────────────────────────────────────┐ │
│   │ Signal   │ Default│ Description                                     │ │
│   ├──────────┼────────┼─────────────────────────────────────────────────┤ │
│   │ SIGCHLD  │ Ignore │ Child process status change                    │ │
│   │ SIGALRM  │ Term   │ Timer from alarm() expired                     │ │
│   │ SIGPIPE  │ Term   │ Broken pipe (no readers)                       │ │
│   │ SIGUSR1  │ Term   │ User-defined signal 1                          │ │
│   │ SIGUSR2  │ Term   │ User-defined signal 2                          │ │
│   │ SIGIO    │ Term   │ I/O possible (async I/O)                       │ │
│   │ SIGURG   │ Ignore │ Urgent data on socket                          │ │
│   │ SIGWINCH │ Ignore │ Window size changed                            │ │
│   └──────────┴────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
│   Default Actions: Term=terminate, Core=terminate+core dump,              │
│                    Stop=stop process, Cont=continue, Ignore=ignore        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Common Signal Handling Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMMON SIGNAL HANDLING PATTERNS                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PATTERN 1: Graceful Shutdown                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   volatile sig_atomic_t shutdown_requested = 0;                           │
│                                                                            │
│   void shutdown_handler(int sig) {                                        │
│       shutdown_requested = 1;                                             │
│   }                                                                       │
│                                                                            │
│   int main() {                                                            │
│       struct sigaction sa = {.sa_handler = shutdown_handler};            │
│       sigemptyset(&sa.sa_mask);                                          │
│       sigaction(SIGTERM, &sa, NULL);                                     │
│       sigaction(SIGINT, &sa, NULL);                                      │
│                                                                            │
│       while (!shutdown_requested) {                                       │
│           process_work();                                                 │
│       }                                                                   │
│       cleanup_and_exit();                                                 │
│   }                                                                       │
│                                                                            │
│                                                                            │
│   PATTERN 2: Reap Child Processes                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void sigchld_handler(int sig) {                                        │
│       int saved_errno = errno;                                           │
│       while (waitpid(-1, NULL, WNOHANG) > 0)                            │
│           ;                                                               │
│       errno = saved_errno;                                               │
│   }                                                                       │
│                                                                            │
│   // Setup with SA_RESTART | SA_NOCLDSTOP                                │
│                                                                            │
│                                                                            │
│   PATTERN 3: Config Reload on SIGHUP                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   volatile sig_atomic_t reload_config = 0;                               │
│                                                                            │
│   void sighup_handler(int sig) {                                         │
│       reload_config = 1;                                                 │
│   }                                                                       │
│                                                                            │
│   // In main loop:                                                        │
│   if (reload_config) {                                                   │
│       reload_config = 0;                                                 │
│       load_configuration();                                              │
│   }                                                                       │
│                                                                            │
│                                                                            │
│   PATTERN 4: Ignore SIGPIPE for Network Servers                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   // At program start:                                                    │
│   signal(SIGPIPE, SIG_IGN);                                              │
│                                                                            │
│   // Then check write() return values for EPIPE                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### sigaction() Flags Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGACTION FLAGS REFERENCE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌──────────────────┬──────────────────────────────────────────────────┐ │
│   │ Flag             │ Effect                                           │ │
│   ├──────────────────┼──────────────────────────────────────────────────┤ │
│   │ SA_SIGINFO       │ Use 3-arg handler (sig, siginfo_t*, context)    │ │
│   │ SA_RESTART       │ Auto-restart interrupted system calls           │ │
│   │ SA_NOCLDSTOP     │ Don't send SIGCHLD when child stops            │ │
│   │ SA_NOCLDWAIT     │ Don't create zombie children                    │ │
│   │ SA_NODEFER       │ Don't block signal during handler               │ │
│   │ SA_RESETHAND     │ Reset to SIG_DFL after handler runs            │ │
│   │ SA_ONSTACK       │ Use alternate signal stack                      │ │
│   └──────────────────┴──────────────────────────────────────────────────┘ │
│                                                                            │
│   COMMON FLAG COMBINATIONS:                                                │
│                                                                            │
│   • SA_RESTART                       - Most handlers                      │
│   • SA_SIGINFO                       - When you need siginfo_t           │
│   • SA_RESTART | SA_NOCLDSTOP        - SIGCHLD handler                   │
│   • SA_SIGINFO | SA_RESTART          - Full info with restart            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Decision Guide: Choosing Signal Handling Approach

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL HANDLING DECISION GUIDE                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                         ┌─────────────────┐                                │
│                         │  Need signals?  │                                │
│                         └────────┬────────┘                                │
│                                  │                                         │
│                    ┌─────────────┴─────────────┐                           │
│                    ▼                           ▼                           │
│            ┌───────────────┐           ┌───────────────┐                   │
│            │ Linux-only?   │           │ POSIX portable │                  │
│            └───────┬───────┘           └───────┬───────┘                   │
│                    │                           │                           │
│          ┌─────────┴─────────┐                 │                           │
│          ▼                   ▼                 ▼                           │
│   ┌─────────────┐    ┌─────────────┐   ┌─────────────┐                    │
│   │ Event loop? │    │ Simple app  │   │ sigaction() │                    │
│   │ (epoll)     │    │             │   │ + patterns  │                    │
│   └──────┬──────┘    └──────┬──────┘   └─────────────┘                    │
│          │                  │                                              │
│          ▼                  ▼                                              │
│   ┌─────────────┐    ┌─────────────┐                                      │
│   │ signalfd()  │    │ sigaction() │                                      │
│   │ with epoll  │    │ or signalfd │                                      │
│   └─────────────┘    └─────────────┘                                      │
│                                                                            │
│                                                                            │
│   MULTI-THREADED PROGRAMS:                                                 │
│   ────────────────────────                                                │
│                                                                            │
│   1. Block all signals in main (before creating threads)                  │
│   2. Use pthread_sigmask() (not sigprocmask)                             │
│   3. Choose one of:                                                       │
│      • Dedicated signal thread with sigwait()                            │
│      • signalfd() with event loop thread                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## References

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REFERENCES AND FURTHER READING                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BOOKS:                                                                   │
│   • "Advanced Programming in the UNIX Environment" - W. Richard Stevens   │
│   • "The Linux Programming Interface" - Michael Kerrisk                   │
│   • "Unix Network Programming" - W. Richard Stevens                       │
│                                                                            │
│   MAN PAGES:                                                               │
│   • signal(7)     - Overview of signals                                   │
│   • sigaction(2)  - Examine and change signal action                      │
│   • sigprocmask(2)- Block/unblock signals                                 │
│   • signalfd(2)   - Create file descriptor for signals (Linux)            │
│   • pidfd_open(2) - Obtain file descriptor for process (Linux)            │
│                                                                            │
│   STANDARDS:                                                               │
│   • POSIX.1-2017 (IEEE Std 1003.1-2017)                                   │
│   • Single UNIX Specification, Version 4                                  │
│                                                                            │
│   ONLINE RESOURCES:                                                        │
│   • Linux man-pages project: https://man7.org/linux/man-pages/           │
│   • POSIX specification: https://pubs.opengroup.org/onlinepubs/9699919799│
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

*Document covers POSIX signals as implemented in Unix-like operating systems,*
*with Linux-specific extensions noted where applicable.*
