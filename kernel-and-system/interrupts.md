# Interrupts in Unix Systems

## A Comprehensive Study of Hardware and Software Interrupt Mechanisms

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Fundamental Concepts](#2-fundamental-concepts)
3. [Types of Interrupts](#3-types-of-interrupts)
4. [Interrupt Hardware Architecture](#4-interrupt-hardware-architecture)
5. [Interrupt Handling Mechanism](#5-interrupt-handling-mechanism)
6. [Kernel Implementation](#6-kernel-implementation)
7. [Software Interrupts and Exceptions](#7-software-interrupts-and-exceptions)
8. [Interrupt Context vs Process Context](#8-interrupt-context-vs-process-context)
9. [Deferred Work Mechanisms](#9-deferred-work-mechanisms)
10. [Advanced Topics](#10-advanced-topics)
11. [Practical Implementation](#11-practical-implementation)
12. [Summary and Reference](#12-summary-and-reference)

---

## 1. Introduction

### The Problem: CPU and Device Speed Mismatch

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE FUNDAMENTAL PROBLEM                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Consider a system where the CPU must communicate with I/O devices:       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CPU Speed:     ~3 GHz = 3,000,000,000 cycles/second              │ │
│   │   Disk Speed:    ~10ms latency = 30,000,000 CPU cycles             │ │
│   │   Network:       ~1ms latency = 3,000,000 CPU cycles               │ │
│   │   Keyboard:      ~100ms between keystrokes = 300,000,000 cycles    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WITHOUT INTERRUPTS (Polling):                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   while (1) {                                                       │ │
│   │       if (keyboard_has_data())     /* Check keyboard */             │ │
│   │           process_keyboard();                                       │ │
│   │       if (disk_ready())            /* Check disk */                 │ │
│   │           process_disk();                                           │ │
│   │       if (network_has_packet())    /* Check network */              │ │
│   │           process_network();                                        │ │
│   │       /* ... check every device ... */                              │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   PROBLEMS:                                                         │ │
│   │   • CPU wastes cycles checking devices that have nothing            │ │
│   │   • Response latency depends on polling frequency                   │ │
│   │   • More devices = more wasted cycles                               │ │
│   │   • Cannot do useful work while waiting                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WITH INTERRUPTS:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CPU: "I'll do useful work. Devices, signal me when ready."        │ │
│   │                                                                     │ │
│   │   /* CPU executing user program */                                  │ │
│   │   ...doing useful computation...                                    │ │
│   │   ...doing useful computation...                                    │ │
│   │   ───── INTERRUPT! Keyboard pressed ─────                           │ │
│   │   /* CPU immediately handles keyboard */                            │ │
│   │   process_keyboard();                                               │ │
│   │   /* CPU returns to computation */                                  │ │
│   │   ...doing useful computation...                                    │ │
│   │                                                                     │ │
│   │   BENEFITS:                                                         │ │
│   │   • Zero wasted cycles polling                                      │ │
│   │   • Immediate response to events                                    │ │
│   │   • CPU does useful work until interrupted                          │ │
│   │   • Scales to any number of devices                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### What is an Interrupt?

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERRUPT DEFINITION                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   An INTERRUPT is an asynchronous signal to the processor indicating       │
│   that an event needs immediate attention. The processor:                  │
│                                                                            │
│   1. Stops what it's currently doing                                       │
│   2. Saves its current state                                               │
│   3. Executes a specific handler for the interrupt                         │
│   4. Restores state and resumes previous execution                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ANALOGY: You're reading a book (executing a program)              │ │
│   │                                                                     │ │
│   │   📖 Reading...reading...reading...                                 │ │
│   │   🔔 DOORBELL RINGS! (interrupt)                                    │ │
│   │   📑 You put a bookmark (save state)                                │ │
│   │   🚶 Go answer door (execute handler)                               │ │
│   │   📖 Return to exact spot (restore state)                           │ │
│   │   📖 Continue reading...                                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY PROPERTIES:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • ASYNCHRONOUS: Can occur at any time, any instruction            │ │
│   │   • TRANSPARENT: Interrupted code doesn't know it was interrupted   │ │
│   │   • PRIORITIZED: Some interrupts are more urgent than others        │ │
│   │   • NESTED: Higher priority can interrupt lower priority handler    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION OF INTERRUPT HANDLING                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1950s: UNIVAC I - First computer with interrupt capability               │
│          Simple "program interrupt" for I/O completion                     │
│                                                                            │
│   1960s: IBM System/360 - Sophisticated interrupt system                   │
│          Multiple interrupt levels, interrupt masking                      │
│                                                                            │
│   1970s: PDP-11 and Unix - Vectored interrupts, priority levels            │
│          Unix established interrupt handling patterns still used today     │
│                                                                            │
│   1980s: Intel 8259 PIC - Programmable Interrupt Controller                │
│          Standard PC interrupt architecture                                │
│                                                                            │
│   1990s: APIC - Advanced Programmable Interrupt Controller                 │
│          Multi-processor interrupt handling, MSI (Message Signaled)        │
│                                                                            │
│   2000s+: MSI-X, Interrupt Virtualization (VT-d)                           │
│           Per-queue interrupts, SR-IOV for virtualization                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Document Organization

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ROADMAP OF THIS DOCUMENT                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   This document progresses from hardware to software, theory to practice:  │
│                                                                            │
│   PART I: CONCEPTS (Sections 2-3)                                          │
│   ├── Fundamental concepts: vectors, handlers, priorities                  │
│   └── Types: hardware/software, maskable/NMI, exceptions                   │
│                                                                            │
│   PART II: HARDWARE (Section 4)                                            │
│   ├── Interrupt controllers: PIC, APIC, I/O APIC                           │
│   └── Interrupt delivery: edge vs level triggered                          │
│                                                                            │
│   PART III: KERNEL MECHANISMS (Sections 5-9)                               │
│   ├── Interrupt handling flow                                              │
│   ├── Kernel data structures (IDT, irq_desc)                               │
│   ├── Exceptions and system calls                                          │
│   ├── Interrupt vs process context                                         │
│   └── Deferred work: softirqs, tasklets, workqueues                        │
│                                                                            │
│   PART IV: ADVANCED & PRACTICAL (Sections 10-12)                           │
│   ├── SMP considerations, threaded IRQs                                    │
│   ├── Writing interrupt handlers                                           │
│   └── Debugging and reference                                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fundamental Concepts

### Interrupt Vectors

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERRUPT VECTORS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   An INTERRUPT VECTOR is a number that identifies a specific interrupt.    │
│   It serves as an index into a table of interrupt handlers.                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   INTERRUPT VECTOR TABLE (or Interrupt Descriptor Table - IDT)      │ │
│   │                                                                     │ │
│   │   Vector │ Handler Address   │ Description                          │ │
│   │   ───────┼───────────────────┼────────────────────────────────────  │ │
│   │     0    │ 0xFFFF8000_1000   │ Divide by Zero                       │ │
│   │     1    │ 0xFFFF8000_1100   │ Debug Exception                      │ │
│   │     2    │ 0xFFFF8000_1200   │ NMI (Non-Maskable Interrupt)         │ │
│   │     3    │ 0xFFFF8000_1300   │ Breakpoint                           │ │
│   │    ...   │ ...               │ ...                                  │ │
│   │    32    │ 0xFFFF8000_3000   │ Timer (IRQ 0)                        │ │
│   │    33    │ 0xFFFF8000_3100   │ Keyboard (IRQ 1)                     │ │
│   │   ...    │ ...               │ ...                                  │ │
│   │   128    │ 0xFFFF8000_8000   │ System Call (int 0x80)               │ │
│   │   ...    │ ...               │ ...                                  │ │
│   │   255    │ 0xFFFF8000_FF00   │ (Last vector)                        │ │
│   │                                                                     │ │
│   │   x86 has 256 interrupt vectors (0-255)                             │ │
│   │   Vectors 0-31: Reserved for CPU exceptions                         │ │
│   │   Vectors 32-255: Available for external interrupts                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   HOW VECTORING WORKS:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. Device raises interrupt on IRQ line                            │ │
│   │   2. Interrupt controller translates IRQ → vector number            │ │
│   │   3. CPU uses vector as index into IDT                              │ │
│   │   4. CPU jumps to handler address from IDT entry                    │ │
│   │                                                                     │ │
│   │   IRQ 1 (Keyboard)                                                  │ │
│   │       │                                                             │ │
│   │       ▼                                                             │ │
│   │   ┌─────────────────┐      ┌─────────────────┐                      │ │
│   │   │ Interrupt       │      │       IDT       │                      │ │
│   │   │ Controller      │─────▶│   [33] ────────────▶ keyboard_handler()│ │
│   │   │ (PIC/APIC)      │      │                 │                      │ │
│   │   │ IRQ 1 → Vec 33  │      │                 │                      │ │
│   │   └─────────────────┘      └─────────────────┘                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Interrupt Service Routines (ISR)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERRUPT SERVICE ROUTINES                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   An ISR (also called interrupt handler) is the code that executes         │
│   when a specific interrupt occurs.                                        │
│                                                                            │
│   ISR REQUIREMENTS:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. FAST: Must complete quickly (microseconds, not milliseconds)   │ │
│   │      - Other interrupts may be blocked while ISR runs               │ │
│   │      - Long ISRs cause system latency                               │ │
│   │                                                                     │ │
│   │   2. NON-BLOCKING: Cannot sleep or wait                             │ │
│   │      - No mutex locks that might sleep                              │ │
│   │      - No memory allocation with GFP_KERNEL                         │ │
│   │      - No disk I/O                                                  │ │
│   │                                                                     │ │
│   │   3. REENTRANT-SAFE: May be interrupted by higher priority          │ │
│   │      - Use spinlocks for shared data (on SMP)                       │ │
│   │      - Disable local interrupts for critical sections               │ │
│   │                                                                     │ │
│   │   4. ACKNOWLEDGE: Must tell hardware interrupt is handled           │ │
│   │      - Write to device register                                     │ │
│   │      - Send EOI to interrupt controller                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TYPICAL ISR STRUCTURE:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   irqreturn_t my_interrupt_handler(int irq, void *dev_id)           │ │
│   │   {                                                                 │ │
│   │       /* 1. Verify this device caused the interrupt */              │ │
│   │       if (!my_device_interrupted(dev_id))                           │ │
│   │           return IRQ_NONE;  /* Not our interrupt */                 │ │
│   │                                                                     │ │
│   │       /* 2. Acknowledge interrupt to hardware */                    │ │
│   │       write_reg(dev_id, ACK_REG, 1);                                │ │
│   │                                                                     │ │
│   │       /* 3. Do minimal work - read status, grab data */             │ │
│   │       status = read_reg(dev_id, STATUS_REG);                        │ │
│   │       data = read_reg(dev_id, DATA_REG);                            │ │
│   │                                                                     │ │
│   │       /* 4. Queue deferred work if needed */                        │ │
│   │       if (needs_processing(status)) {                               │ │
│   │           enqueue_work(data);                                       │ │
│   │           tasklet_schedule(&my_tasklet);                            │ │
│   │       }                                                             │ │
│   │                                                                     │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Priority and Masking

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERRUPT PRIORITY AND MASKING                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PRIORITY LEVELS:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Not all interrupts are equally important. Priority determines:    │ │
│   │   • Which interrupt is serviced first when multiple pending         │ │
│   │   • Whether an interrupt can preempt another interrupt's handler    │ │
│   │                                                                     │ │
│   │   TYPICAL PRIORITY (highest to lowest):                             │ │
│   │                                                                     │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │  Machine Check (hardware failure)           HIGHEST          │  │ │
│   │   │  NMI (Non-Maskable Interrupt)                 ▲              │  │ │
│   │   │  Debug exceptions                             │              │  │ │
│   │   │  Performance monitoring                       │              │  │ │
│   │   │  Inter-processor interrupts (IPI)             │              │  │ │
│   │   │  Timer interrupt                              │              │  │ │
│   │   │  I/O device interrupts                        │              │  │ │
│   │   │  Software interrupts (softirq)                ▼              │  │ │
│   │   │  Normal process execution                   LOWEST           │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   INTERRUPT MASKING:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Masking = temporarily disabling interrupts                        │ │
│   │                                                                     │ │
│   │   LOCAL MASKING (this CPU only):                                    │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │                                                              │  │ │
│   │   │   /* x86: CLI (Clear Interrupt Flag) */                      │  │ │
│   │   │   local_irq_disable();   /* Disable all maskable interrupts */│  │ │
│   │   │   /* critical section - cannot be interrupted */             │  │ │
│   │   │   local_irq_enable();    /* Re-enable interrupts */          │  │ │
│   │   │                                                              │  │ │
│   │   │   /* Save and restore flags version: */                      │  │ │
│   │   │   unsigned long flags;                                       │  │ │
│   │   │   local_irq_save(flags);     /* Save IF, then disable */     │  │ │
│   │   │   /* critical section */                                     │  │ │
│   │   │   local_irq_restore(flags);  /* Restore previous IF state */ │  │ │
│   │   │                                                              │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   SPECIFIC IRQ MASKING:                                             │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │                                                              │  │ │
│   │   │   disable_irq(irq);     /* Disable specific IRQ, wait */     │  │ │
│   │   │   disable_irq_nosync(irq); /* Disable, don't wait */         │  │ │
│   │   │   enable_irq(irq);      /* Re-enable specific IRQ */         │  │ │
│   │   │                                                              │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY MASK INTERRUPTS?                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Protect data structures being modified                          │ │
│   │   • Prevent infinite interrupt recursion                            │ │
│   │   • Ensure atomic operations complete                               │ │
│   │   • Coordinate between interrupt handler and main code              │ │
│   │                                                                     │ │
│   │   WARNING: Keep masked time SHORT! Missed interrupts = lost data    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Types of Interrupts

### Hardware vs Software Interrupts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HARDWARE VS SOFTWARE INTERRUPTS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   HARDWARE INTERRUPTS (External/Asynchronous)                       │ │
│   │   ═══════════════════════════════════════════                       │ │
│   │                                                                     │ │
│   │   • Generated by external hardware devices                          │ │
│   │   • Asynchronous: can occur at ANY instruction boundary             │ │
│   │   • Signal delivered via physical interrupt lines (IRQ)             │ │
│   │                                                                     │ │
│   │   Examples:                                                         │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  Timer chip        → Periodic tick for scheduling          │    │ │
│   │   │  Keyboard          → Key press/release                     │    │ │
│   │   │  Network card      → Packet arrived                        │    │ │
│   │   │  Disk controller   → I/O operation complete                │    │ │
│   │   │  USB controller    → Device connected/data ready           │    │ │
│   │   │  GPU               → Frame rendered                        │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                         CPU                                 │   │ │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │ │
│   │   │   │  Executing instruction N                            │   │   │ │
│   │   │   │  Executing instruction N+1                          │   │   │ │
│   │   │   │  ══════════ IRQ PIN ASSERTED ══════════             │   │   │ │
│   │   │   │  Check pending interrupts (between instructions)    │   │   │ │
│   │   │   │  Save state, jump to handler                        │   │   │ │
│   │   │   └─────────────────────────────────────────────────────┘   │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SOFTWARE INTERRUPTS (Internal/Synchronous)                        │ │
│   │   ═══════════════════════════════════════════                       │ │
│   │                                                                     │ │
│   │   • Generated by CPU itself or by software instruction              │ │
│   │   • Synchronous: occur at specific, predictable points              │ │
│   │   • Triggered by INT instruction or CPU detecting an error          │ │
│   │                                                                     │ │
│   │   Examples:                                                         │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  int 0x80          → System call (Linux legacy)            │    │ │
│   │   │  syscall           → System call (modern)                  │    │ │
│   │   │  Division by zero  → CPU exception                         │    │ │
│   │   │  Page fault        → Memory not present                    │    │ │
│   │   │  int 3             → Debugger breakpoint                   │    │ │
│   │   │  Illegal opcode    → Invalid instruction                   │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │  mov eax, 1           /* Normal instruction */              │   │ │
│   │   │  int 0x80             /* ← THIS instruction triggers it */  │   │ │
│   │   │  /* Handler runs */                                         │   │ │
│   │   │  /* Returns here */                                         │   │ │
│   │   │  mov ebx, eax         /* Continues after */                 │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Maskable vs Non-Maskable Interrupts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MASKABLE VS NON-MASKABLE INTERRUPTS                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   MASKABLE INTERRUPTS (INTR)                                        │ │
│   │   ═══════════════════════════                                       │ │
│   │                                                                     │ │
│   │   • Can be temporarily disabled (masked) by software                │ │
│   │   • Controlled by CPU's Interrupt Flag (IF) in FLAGS register       │ │
│   │   • CLI instruction clears IF → interrupts disabled                 │ │
│   │   • STI instruction sets IF → interrupts enabled                    │ │
│   │                                                                     │ │
│   │   When masked:                                                      │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │   Device raises IRQ                                        │    │ │
│   │   │       ↓                                                    │    │ │
│   │   │   IRQ held pending by interrupt controller                 │    │ │
│   │   │       ↓                                                    │    │ │
│   │   │   (CPU continues, interrupts disabled)                     │    │ │
│   │   │       ↓                                                    │    │ │
│   │   │   CPU enables interrupts (STI)                             │    │ │
│   │   │       ↓                                                    │    │ │
│   │   │   Pending IRQ delivered, handler runs                      │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   │   Most device interrupts are maskable: keyboard, disk, network      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   NON-MASKABLE INTERRUPTS (NMI)                                     │ │
│   │   ═════════════════════════════                                     │ │
│   │                                                                     │ │
│   │   • CANNOT be disabled by software - always delivered               │ │
│   │   • Reserved for critical, urgent conditions                        │ │
│   │   • Has its own CPU pin (NMI pin)                                   │ │
│   │   • Vector 2 on x86                                                 │ │
│   │                                                                     │ │
│   │   Uses:                                                             │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  Memory parity errors    → Hardware failure                │    │ │
│   │   │  Hardware watchdog       → System hang detection           │    │ │
│   │   │  System management       → SMI (firmware)                  │    │ │
│   │   │  Debugger break          → Breaking into debugger          │    │ │
│   │   │  Power failure warning   → Save state before power loss    │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   CPU with IF=0 (interrupts disabled)                       │   │ │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │ │
│   │   │   │  IRQ arrives → IGNORED (masked)                     │   │   │ │
│   │   │   │  NMI arrives → ALWAYS HANDLED                       │   │   │ │
│   │   │   └─────────────────────────────────────────────────────┘   │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Exceptions: Faults, Traps, and Aborts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CPU EXCEPTIONS                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Exceptions are synchronous interrupts generated by the CPU when it       │
│   detects an error or special condition during instruction execution.      │
│                                                                            │
│   THREE TYPES OF EXCEPTIONS:                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   FAULT                                                             │ │
│   │   ═════                                                             │ │
│   │   • Potentially recoverable error                                   │ │
│   │   • Return address = faulting instruction (will re-execute)         │ │
│   │   • Handler can fix the problem, then restart instruction           │ │
│   │                                                                     │ │
│   │   Examples:                                                         │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  Page Fault (#PF, vector 14)                               │    │ │
│   │   │    → Page not present, handler loads page, retries access  │    │ │
│   │   │  General Protection Fault (#GP, vector 13)                 │    │ │
│   │   │    → Privilege violation, usually fatal                    │    │ │
│   │   │  Segment Not Present (#NP, vector 11)                      │    │ │
│   │   │    → Handler can load segment                              │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │   mov eax, [addr]    ← Page fault here                      │   │ │
│   │   │      │                                                      │   │ │
│   │   │      └──▶ Handler: load page from disk                      │   │ │
│   │   │               │                                             │   │ │
│   │   │               └──▶ Return: re-execute "mov eax, [addr]"     │   │ │
│   │   │                       │                                     │   │ │
│   │   │                       └──▶ Now succeeds!                    │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   TRAP                                                              │ │
│   │   ════                                                              │ │
│   │   • Intentional exception, often for debugging or system calls      │ │
│   │   • Return address = NEXT instruction (don't re-execute)            │ │
│   │   • Reported immediately after trapping instruction completes       │ │
│   │                                                                     │ │
│   │   Examples:                                                         │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  Breakpoint (#BP, vector 3)                                │    │ │
│   │   │    → INT 3 instruction for debuggers                       │    │ │
│   │   │  Overflow (#OF, vector 4)                                  │    │ │
│   │   │    → INTO instruction when OF flag set                     │    │ │
│   │   │  Debug (#DB, vector 1)                                     │    │ │
│   │   │    → Single-step, hardware breakpoints                     │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │   int 3              ← Breakpoint trap                      │   │ │
│   │   │   mov ebx, 1         ← Handler returns HERE                 │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ABORT                                                             │ │
│   │   ═════                                                             │ │
│   │   • Severe, unrecoverable error                                     │ │
│   │   • Cannot reliably determine faulting instruction                  │ │
│   │   • Usually terminates the process or panics the system             │ │
│   │                                                                     │ │
│   │   Examples:                                                         │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  Double Fault (#DF, vector 8)                              │    │ │
│   │   │    → Exception while handling exception                    │    │ │
│   │   │  Machine Check (#MC, vector 18)                            │    │ │
│   │   │    → Uncorrectable hardware error                          │    │ │
│   │   │  Triple Fault                                              │    │ │
│   │   │    → Exception while handling double fault → CPU RESET     │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### x86 Exception Table

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    x86 EXCEPTION VECTORS (0-31)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌────────┬────────────────────────────┬────────────┬─────────────────┐   │
│   │ Vector │ Name                       │ Type       │ Error Code?     │   │
│   ├────────┼────────────────────────────┼────────────┼─────────────────┤   │
│   │   0    │ Divide Error (#DE)         │ Fault      │ No              │   │
│   │   1    │ Debug (#DB)                │ Fault/Trap │ No              │   │
│   │   2    │ NMI                        │ Interrupt  │ No              │   │
│   │   3    │ Breakpoint (#BP)           │ Trap       │ No              │   │
│   │   4    │ Overflow (#OF)             │ Trap       │ No              │   │
│   │   5    │ Bound Range (#BR)          │ Fault      │ No              │   │
│   │   6    │ Invalid Opcode (#UD)       │ Fault      │ No              │   │
│   │   7    │ Device Not Avail (#NM)     │ Fault      │ No              │   │
│   │   8    │ Double Fault (#DF)         │ Abort      │ Yes (zero)      │   │
│   │   9    │ (reserved)                 │ -          │ -               │   │
│   │  10    │ Invalid TSS (#TS)          │ Fault      │ Yes             │   │
│   │  11    │ Segment Not Present (#NP)  │ Fault      │ Yes             │   │
│   │  12    │ Stack Fault (#SS)          │ Fault      │ Yes             │   │
│   │  13    │ General Protection (#GP)   │ Fault      │ Yes             │   │
│   │  14    │ Page Fault (#PF)           │ Fault      │ Yes             │   │
│   │  15    │ (reserved)                 │ -          │ -               │   │
│   │  16    │ x87 FPU Error (#MF)        │ Fault      │ No              │   │
│   │  17    │ Alignment Check (#AC)      │ Fault      │ Yes (zero)      │   │
│   │  18    │ Machine Check (#MC)        │ Abort      │ No              │   │
│   │  19    │ SIMD FP Exception (#XM)    │ Fault      │ No              │   │
│   │  20    │ Virtualization (#VE)       │ Fault      │ No              │   │
│   │ 21-31  │ (reserved by Intel)        │ -          │ -               │   │
│   └────────┴────────────────────────────┴────────────┴─────────────────┘   │
│                                                                            │
│   Vectors 32-255: Available for external interrupts and software use       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Interrupt Hardware Architecture

### Programmable Interrupt Controller (PIC)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    8259 PROGRAMMABLE INTERRUPT CONTROLLER                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The original IBM PC used the Intel 8259 PIC. Modern systems still        │
│   emulate it for compatibility, though APIC is now preferred.              │
│                                                                            │
│   ARCHITECTURE (Cascaded dual PIC):                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌─────────────┐         ┌─────────────┐                           │ │
│   │   │ IRQ 0 Timer │────┐    │ IRQ 8 RTC   │────┐                      │ │
│   │   │ IRQ 1 Keybd │────┤    │ IRQ 9       │────┤                      │ │
│   │   │ IRQ 2 ──────│─┐  │    │ IRQ 10      │────┤                      │ │
│   │   │ IRQ 3 COM2  │ │  │    │ IRQ 11      │────┤                      │ │
│   │   │ IRQ 4 COM1  │ │  │    │ IRQ 12 Mouse│────┤                      │ │
│   │   │ IRQ 5 LPT2  │ │  ├───▶│ IRQ 13 FPU  │────┼───▶  Slave PIC       │ │
│   │   │ IRQ 6 Floppy│ │  │    │ IRQ 14 IDE1 │────┤      8259            │ │
│   │   │ IRQ 7 LPT1  │ │  │    │ IRQ 15 IDE2 │────┘                      │ │
│   │   └─────────────┘ │  │    └─────────────┘                           │ │
│   │                   │  │           │                                   │ │
│   │    Master PIC     │  │           │                                   │ │
│   │      8259    ◀────┘  │           │ (Cascade: IRQ2 chains to slave)   │ │
│   │         │            │           │                                   │ │
│   │         │            │           │                                   │ │
│   │         └────────────┴───────────┴──────────▶  CPU INTR pin          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PIC OPERATION:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. Device asserts IRQ line (e.g., keyboard on IRQ1)               │ │
│   │   2. PIC sets corresponding bit in Interrupt Request Register (IRR) │ │
│   │   3. PIC checks priority vs In-Service Register (ISR)               │ │
│   │   4. If higher priority, PIC asserts INT to CPU                     │ │
│   │   5. CPU acknowledges (INTA cycle)                                  │ │
│   │   6. PIC sends interrupt vector number to CPU                       │ │
│   │   7. PIC sets bit in ISR, clears IRR bit                            │ │
│   │   8. CPU calls handler at IDT[vector]                               │ │
│   │   9. Handler sends EOI (End of Interrupt) to PIC                    │ │
│   │   10. PIC clears ISR bit, ready for next interrupt                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PROGRAMMING THE PIC:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   I/O Ports:                                                        │ │
│   │   • Master PIC: 0x20 (command), 0x21 (data)                         │ │
│   │   • Slave PIC:  0xA0 (command), 0xA1 (data)                         │ │
│   │                                                                     │ │
│   │   /* Send EOI to master PIC */                                      │ │
│   │   outb(0x20, 0x20);                                                 │ │
│   │                                                                     │ │
│   │   /* Mask IRQ 3 (disable) */                                        │ │
│   │   mask = inb(0x21);                                                 │ │
│   │   outb(0x21, mask | (1 << 3));                                      │ │
│   │                                                                     │ │
│   │   /* Remap PIC vectors (during boot) */                             │ │
│   │   /* Master: IRQ 0-7 → vectors 32-39 */                             │ │
│   │   /* Slave:  IRQ 8-15 → vectors 40-47 */                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LIMITATIONS OF PIC:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Only 15 usable IRQs (16 minus cascade)                          │ │
│   │   • Single CPU only - no SMP support                                │ │
│   │   • Fixed priority (IRQ0 highest, IRQ7 lowest per PIC)              │ │
│   │   • No message-signaled interrupts                                  │ │
│   │   • Slow: requires I/O port access                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Advanced Programmable Interrupt Controller (APIC)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ADVANCED PROGRAMMABLE INTERRUPT CONTROLLER             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   APIC was introduced to overcome PIC limitations and support SMP systems. │
│   It consists of two components: Local APIC (per-CPU) and I/O APIC.        │
│                                                                            │
│   APIC ARCHITECTURE:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │                         System Bus / APIC Bus                       │ │
│   │   ════════════════════════════════════════════════════════════════  │ │
│   │         │              │              │              │               │ │
│   │         ▼              ▼              ▼              ▼               │ │
│   │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐     │ │
│   │   │  Local   │   │  Local   │   │  Local   │   │              │     │ │
│   │   │  APIC    │   │  APIC    │   │  APIC    │   │   I/O APIC   │     │ │
│   │   │  (CPU 0) │   │  (CPU 1) │   │  (CPU 2) │   │              │     │ │
│   │   └────┬─────┘   └────┬─────┘   └────┬─────┘   └──────┬───────┘     │ │
│   │        │              │              │                │              │ │
│   │        ▼              ▼              ▼                │              │ │
│   │   ┌────────┐    ┌────────┐    ┌────────┐             │              │ │
│   │   │ CPU 0  │    │ CPU 1  │    │ CPU 2  │             │              │ │
│   │   └────────┘    └────────┘    └────────┘             │              │ │
│   │                                                      │              │ │
│   │        External Device IRQs ─────────────────────────┘              │ │
│   │        (keyboard, disk, network, etc.)                              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LOCAL APIC (one per CPU):                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Functions:                                                        │ │
│   │   • Receives interrupts from I/O APIC                               │ │
│   │   • Receives Inter-Processor Interrupts (IPI)                       │ │
│   │   • Contains local timer for each CPU                               │ │
│   │   • Handles local interrupt sources (LINT0, LINT1)                  │ │
│   │   • Prioritizes and delivers interrupts to CPU core                 │ │
│   │                                                                     │ │
│   │   Key Registers (memory-mapped at 0xFEE00000):                      │ │
│   │   ┌────────────────────┬──────────┬───────────────────────────┐     │ │
│   │   │ Register           │ Offset   │ Purpose                   │     │ │
│   │   ├────────────────────┼──────────┼───────────────────────────┤     │ │
│   │   │ ID                 │ 0x020    │ Local APIC ID             │     │ │
│   │   │ Version            │ 0x030    │ Version and max LVT entry │     │ │
│   │   │ TPR                │ 0x080    │ Task Priority Register    │     │ │
│   │   │ EOI                │ 0x0B0    │ End of Interrupt          │     │ │
│   │   │ Spurious           │ 0x0F0    │ Spurious interrupt vector │     │ │
│   │   │ ICR                │ 0x300    │ Interrupt Command (IPI)   │     │ │
│   │   │ LVT Timer          │ 0x320    │ Local timer config        │     │ │
│   │   │ LVT LINT0          │ 0x350    │ Local interrupt 0         │     │ │
│   │   │ LVT LINT1          │ 0x360    │ Local interrupt 1         │     │ │
│   │   └────────────────────┴──────────┴───────────────────────────┘     │ │
│   │                                                                     │ │
│   │   /* Send EOI to local APIC (much simpler than PIC!) */             │ │
│   │   void apic_eoi(void) {                                             │ │
│   │       *(volatile uint32_t *)(APIC_BASE + 0x0B0) = 0;                │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   I/O APIC (typically one per system):                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Functions:                                                        │ │
│   │   • Receives external device interrupts (IRQs)                      │ │
│   │   • Routes interrupts to specific CPU(s) via Local APIC             │ │
│   │   • Supports 24 interrupt pins (vs PIC's 15)                        │ │
│   │   • Programmable routing and priority                               │ │
│   │                                                                     │ │
│   │   I/O APIC Routing (Redirection Table):                             │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  Each entry (64 bits) specifies:                           │    │ │
│   │   │  • Vector number (0-255)                                   │    │ │
│   │   │  • Delivery mode (fixed, lowest priority, SMI, NMI)        │    │ │
│   │   │  • Destination mode (physical or logical)                  │    │ │
│   │   │  • Destination (which CPU(s) receive interrupt)            │    │ │
│   │   │  • Trigger mode (edge or level)                            │    │ │
│   │   │  • Mask bit                                                │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   │   Example: Route IRQ 1 (keyboard) to CPU 0, vector 33:              │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  ioapic_write(IOREDTBL + 1*2,     // low 32 bits           │    │ │
│   │   │               0x00000021);         // vector 33, fixed     │    │ │
│   │   │  ioapic_write(IOREDTBL + 1*2 + 1, // high 32 bits          │    │ │
│   │   │               0x00000000);         // dest = CPU 0         │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Inter-Processor Interrupts (IPI)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTER-PROCESSOR INTERRUPTS (IPI)                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   IPIs allow CPUs to signal each other - essential for SMP coordination.   │
│                                                                            │
│   COMMON IPI USES:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • TLB shootdown: "Invalidate these page table entries"            │ │
│   │   • Scheduler: "Run this process" or "Reschedule"                   │ │
│   │   • Function call: "Execute this function on your CPU"              │ │
│   │   • STOP: "Halt for debugging or shutdown"                          │ │
│   │   • Performance: "Start/stop performance counters"                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SENDING AN IPI:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Write to Interrupt Command Register (ICR):                        │ │
│   │                                                                     │ │
│   │   /* Send IPI vector 0xFE to CPU 2 */                               │ │
│   │   apic_write(ICR_HIGH, 2 << 24);    // destination CPU 2            │ │
│   │   apic_write(ICR_LOW, 0x000000FE);  // vector 0xFE, fixed delivery  │ │
│   │                                                                     │ │
│   │   Delivery Modes:                                                   │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  000 = Fixed       - deliver to specified vector           │    │ │
│   │   │  001 = Lowest Pri  - deliver to lowest priority CPU        │    │ │
│   │   │  010 = SMI         - System Management Interrupt           │    │ │
│   │   │  100 = NMI         - Non-maskable interrupt                │    │ │
│   │   │  101 = INIT        - INIT signal (reset CPU)               │    │ │
│   │   │  110 = Startup     - Startup IPI (SIPI) for CPU init       │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TLB SHOOTDOWN EXAMPLE:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CPU 0                           CPU 1, 2, 3                       │ │
│   │   ─────                           ───────────                       │ │
│   │   Modifies page table                                               │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   Sends IPI to all CPUs ────────▶ Receive IPI                       │ │
│   │        │                               │                            │ │
│   │        │                               ▼                            │ │
│   │        │                          Invalidate TLB                    │ │
│   │        │                          (invlpg or full flush)            │ │
│   │        │                               │                            │ │
│   │        │                               ▼                            │ │
│   │   Waits for ack ◀──────────────── Signal completion                 │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   Continue execution                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Message Signaled Interrupts (MSI/MSI-X)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MESSAGE SIGNALED INTERRUPTS (MSI/MSI-X)                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   MSI replaces physical interrupt lines with memory writes - the modern    │
│   way to deliver interrupts, especially for PCIe devices.                  │
│                                                                            │
│   TRADITIONAL INTERRUPTS vs MSI:                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   TRADITIONAL (pin-based):                                          │ │
│   │   ┌────────────┐         ┌─────────────┐         ┌────────────┐     │ │
│   │   │   Device   │──IRQ───▶│   I/O APIC  │──msg───▶│ Local APIC │     │ │
│   │   └────────────┘  line   └─────────────┘         └────────────┘     │ │
│   │                                                                     │ │
│   │   • Requires physical wires                                         │ │
│   │   • Limited pins (24 on I/O APIC)                                   │ │
│   │   • Must be shared among multiple devices                           │ │
│   │                                                                     │ │
│   │   MSI (message-based):                                              │ │
│   │   ┌────────────┐                                 ┌────────────┐     │ │
│   │   │   Device   │──memory write (PCI)───────────▶│ Local APIC │     │ │
│   │   └────────────┘                                 └────────────┘     │ │
│   │                                                                     │ │
│   │   • No physical interrupt lines needed                              │ │
│   │   • Each device can have unique vectors                             │ │
│   │   • Device writes to special memory address                         │ │
│   │   • Address encodes destination CPU(s)                              │ │
│   │   • Data encodes interrupt vector                                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MSI MESSAGE FORMAT:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Address (where device writes):                                    │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  0xFEE[dest_id][RH][DM]0000                                │    │ │
│   │   │                                                            │    │ │
│   │   │  0xFEE     = Local APIC address base                       │    │ │
│   │   │  dest_id   = Destination CPU ID (bits 19:12)               │    │ │
│   │   │  RH        = Redirection hint (bit 3)                      │    │ │
│   │   │  DM        = Destination mode (bit 2)                      │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   │   Data (what device writes):                                        │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │  Bits 7:0   = Vector number                                │    │ │
│   │   │  Bits 10:8  = Delivery mode (000=fixed, 001=lowest pri)    │    │ │
│   │   │  Bit 14     = Level (0=deassert, 1=assert)                 │    │ │
│   │   │  Bit 15     = Trigger mode (0=edge, 1=level)               │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MSI vs MSI-X:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌──────────────────────┬────────────────────────────────────┐     │ │
│   │   │ Feature              │ MSI          │ MSI-X               │     │ │
│   │   ├──────────────────────┼──────────────┼─────────────────────┤     │ │
│   │   │ Max vectors          │ 32           │ 2048                │     │ │
│   │   │ Vector assignment    │ Consecutive  │ Independent         │     │ │
│   │   │ Per-vector masking   │ No (MSI 2.2) │ Yes                 │     │ │
│   │   │ CPU targeting        │ All same     │ Per-vector          │     │ │
│   │   └──────────────────────┴──────────────┴─────────────────────┘     │ │
│   │                                                                     │ │
│   │   MSI-X is preferred for high-performance devices (NVMe, NICs)      │ │
│   │   that need multiple independent interrupt vectors.                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ADVANTAGES OF MSI:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. No interrupt sharing - each device gets unique vector(s)       │ │
│   │   2. Lower latency - no I/O APIC lookup                             │ │
│   │   3. Automatic load balancing possible (lowest priority delivery)   │ │
│   │   4. Better scaling - supports many more interrupt sources          │ │
│   │   5. Implicit ordering with DMA - interrupt arrives after data      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Edge vs Level Triggered Interrupts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EDGE vs LEVEL TRIGGERED INTERRUPTS                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Two fundamentally different ways to signal an interrupt condition:       │
│                                                                            │
│   EDGE TRIGGERED:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Signal: ────────┐         ┌───────────────────────────────────    │ │
│   │                   │         │                                       │ │
│   │                   └─────────┘                                       │ │
│   │                   ↑                                                 │ │
│   │                   Interrupt detected here (transition)              │ │
│   │                                                                     │ │
│   │   Characteristics:                                                  │ │
│   │   • Interrupt detected on signal TRANSITION (low→high or high→low) │ │
│   │   • One interrupt per edge, regardless of signal duration           │ │
│   │   • Device must deassert and reassert for another interrupt         │ │
│   │   • Cannot be shared (easily) - edge might be missed                │ │
│   │                                                                     │ │
│   │   Advantages:                                                       │ │
│   │   • Simple hardware                                                 │ │
│   │   • No EOI timing issues                                            │ │
│   │   • Fast - handler doesn't need to ack device immediately           │ │
│   │                                                                     │ │
│   │   Disadvantages:                                                    │ │
│   │   • Can lose interrupts if edge occurs while masked                 │ │
│   │   • Difficult to share among multiple devices                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LEVEL TRIGGERED:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Signal: ────────┐                             ┌───────────────    │ │
│   │                   │                             │                   │ │
│   │                   └─────────────────────────────┘                   │ │
│   │                   ←── Interrupt asserted ──────→                    │ │
│   │                       (continuously active)                         │ │
│   │                                                                     │ │
│   │   Characteristics:                                                  │ │
│   │   • Interrupt detected while signal is at active LEVEL              │ │
│   │   • Re-interrupts immediately if still asserted after EOI           │ │
│   │   • Handler MUST make device deassert before EOI                    │ │
│   │   • Can be shared - handler checks which device(s) need service     │ │
│   │                                                                     │ │
│   │   Advantages:                                                       │ │
│   │   • Cannot lose interrupts - signal stays asserted                  │ │
│   │   • Easy to share among multiple devices                            │ │
│   │   • Robust - will re-interrupt if not properly handled              │ │
│   │                                                                     │ │
│   │   Disadvantages:                                                    │ │
│   │   • Handler must ack device before EOI (ordering constraints)       │ │
│   │   • Can cause interrupt storm if device not acked                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SHARED LEVEL-TRIGGERED INTERRUPT:                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Device A ───┐                                                     │ │
│   │               ├──OR──▶ IRQ line ──▶ I/O APIC                        │ │
│   │   Device B ───┘         (wired-OR)                                  │ │
│   │                                                                     │ │
│   │   Handler must:                                                     │ │
│   │   1. Check Device A - if interrupting, service it                   │ │
│   │   2. Check Device B - if interrupting, service it                   │ │
│   │   3. Loop until no devices need service                             │ │
│   │   4. Send EOI                                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Interrupt Handling Mechanism

### CPU State During Interrupt

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CPU STATE DURING INTERRUPT                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When an interrupt occurs, the CPU must save state and transfer control   │
│   to the handler. This happens in hardware and is called the "interrupt    │
│   frame" or "trap frame".                                                  │
│                                                                            │
│   HARDWARE-SAVED STATE (x86-64):                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Stack after interrupt (growing downward):                         │ │
│   │                                                                     │ │
│   │   ┌──────────────────────────────────────────────┐  ← old RSP       │ │
│   │   │           (old stack contents)               │                  │ │
│   │   ├──────────────────────────────────────────────┤                  │ │
│   │   │                   SS                         │  +40             │ │
│   │   ├──────────────────────────────────────────────┤                  │ │
│   │   │                   RSP                        │  +32             │ │
│   │   ├──────────────────────────────────────────────┤                  │ │
│   │   │                  RFLAGS                      │  +24             │ │
│   │   ├──────────────────────────────────────────────┤                  │ │
│   │   │                   CS                         │  +16             │ │
│   │   ├──────────────────────────────────────────────┤                  │ │
│   │   │                   RIP                        │  +8              │ │
│   │   ├──────────────────────────────────────────────┤                  │ │
│   │   │           Error Code (if any)                │  +0  ← new RSP   │ │
│   │   └──────────────────────────────────────────────┘                  │ │
│   │                                                                     │ │
│   │   Note: SS and RSP only pushed if privilege level changes           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOFTWARE-SAVED STATE (kernel handler prologue):                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Typical handler entry - save ALL registers */                  │ │
│   │   ENTRY(irq_common_handler)                                         │ │
│   │       push %rax                                                     │ │
│   │       push %rbx                                                     │ │
│   │       push %rcx                                                     │ │
│   │       push %rdx                                                     │ │
│   │       push %rsi                                                     │ │
│   │       push %rdi                                                     │ │
│   │       push %rbp                                                     │ │
│   │       push %r8                                                      │ │
│   │       push %r9                                                      │ │
│   │       push %r10                                                     │ │
│   │       push %r11                                                     │ │
│   │       push %r12                                                     │ │
│   │       push %r13                                                     │ │
│   │       push %r14                                                     │ │
│   │       push %r15                                                     │ │
│   │       /* Now call C handler */                                      │ │
│   │       mov %rsp, %rdi          /* pt_regs pointer */                 │ │
│   │       call do_IRQ                                                   │ │
│   │       /* ... restore and iretq ... */                               │ │
│   │   END(irq_common_handler)                                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Complete Interrupt Flow

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE INTERRUPT FLOW                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DETAILED SEQUENCE:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. INTERRUPT OCCURS                                               │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │ • Device raises IRQ line (or MSI write)                   │     │ │
│   │   │ • Interrupt controller (APIC) receives request            │     │ │
│   │   │ • APIC prioritizes and delivers to CPU                    │     │ │
│   │   │ • CPU checks IF flag and compares priority                │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                      │                                              │ │
│   │                      ▼                                              │ │
│   │   2. CPU HARDWARE ACTIONS (atomic, cannot be interrupted)           │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │ a) Finish current instruction                             │     │ │
│   │   │ b) Read vector number from interrupt controller           │     │ │
│   │   │ c) Look up IDT[vector] for handler address and DPL        │     │ │
│   │   │ d) Check privileges (current CPL vs gate DPL)             │     │ │
│   │   │ e) If ring 3→ring 0: load new SS:RSP from TSS             │     │ │
│   │   │ f) Push SS, RSP, RFLAGS, CS, RIP (and error code)         │     │ │
│   │   │ g) Clear IF (disable interrupts) and TF (single-step)     │     │ │
│   │   │ h) Load CS:RIP from IDT entry (jump to handler)           │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                      │                                              │ │
│   │                      ▼                                              │ │
│   │   3. KERNEL ENTRY (assembly stub)                                   │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │ • Save all general-purpose registers                      │     │ │
│   │   │ • Save segment registers if needed                        │     │ │
│   │   │ • Set up kernel data segments                             │     │ │
│   │   │ • Call C handler with pt_regs pointer                     │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                      │                                              │ │
│   │                      ▼                                              │ │
│   │   4. INTERRUPT HANDLER (C code)                                     │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │ • Acknowledge interrupt at device level                   │     │ │
│   │   │ • Read device status/data                                 │     │ │
│   │   │ • Queue work for later (bottom half) if needed            │     │ │
│   │   │ • Send EOI to interrupt controller                        │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                      │                                              │ │
│   │                      ▼                                              │ │
│   │   5. RETURN FROM INTERRUPT                                          │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │ • Check for pending softirqs/work                         │     │ │
│   │   │ • Check if rescheduling needed (TIF_NEED_RESCHED)         │     │ │
│   │   │ • Restore all saved registers                             │     │ │
│   │   │ • Execute IRETQ instruction                               │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   VISUAL TIMELINE:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   User Process         Kernel                      Device           │ │
│   │   ────────────         ──────                      ──────           │ │
│   │        │                                              │             │ │
│   │        │  running                                     │             │ │
│   │        │                                              │             │ │
│   │        │◀───────────────────────────────────────────IRQ             │ │
│   │        │                                                            │ │
│   │   ─────┼─────────── interrupt gate ──────────────────────           │ │
│   │        │                  │                                         │ │
│   │        │                  ▼                                         │ │
│   │        │             save state                                     │ │
│   │        │                  │                                         │ │
│   │        │                  ▼                                         │ │
│   │        │             do_IRQ()                                       │ │
│   │        │                  │                                         │ │
│   │        │                  ├─────────────────────────────ack─────▶   │ │
│   │        │                  │                                         │ │
│   │        │                  ▼                                         │ │
│   │        │             queue work                                     │ │
│   │        │                  │                                         │ │
│   │        │                  ▼                                         │ │
│   │        │              send EOI                                      │ │
│   │        │                  │                                         │ │
│   │        │                  ▼                                         │ │
│   │        │            restore state                                   │ │
│   │        │                  │                                         │ │
│   │   ─────┼─────────────── iretq ───────────────────────────           │ │
│   │        │                                                            │ │
│   │        ▼  continues                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Return from Interrupt (IRET)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RETURN FROM INTERRUPT (IRET/IRETQ)                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The IRET instruction atomically restores CPU state and returns to        │
│   the interrupted context.                                                 │
│                                                                            │
│   IRET ACTIONS:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. Pop RIP from stack                                             │ │
│   │   2. Pop CS from stack (includes CPL)                               │ │
│   │   3. Pop RFLAGS from stack                                          │ │
│   │   4. If returning to different privilege level:                     │ │
│   │      a. Pop RSP from stack                                          │ │
│   │      b. Pop SS from stack                                           │ │
│   │   5. Resume execution at restored CS:RIP with restored RFLAGS       │ │
│   │                                                                     │ │
│   │   /* Assembly example */                                            │ │
│   │   irq_return:                                                       │ │
│   │       pop %r15                                                      │ │
│   │       pop %r14                                                      │ │
│   │       ... /* restore all saved registers */                         │ │
│   │       pop %rax                                                      │ │
│   │       addq $8, %rsp      /* skip error code if present */           │ │
│   │       iretq              /* return from interrupt */                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SECURITY CONSIDERATIONS:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   The kernel must be careful when returning to user mode:           │ │
│   │                                                                     │ │
│   │   • SMAP/SMEP checks restored (can't access user memory)            │ │
│   │   • User-mode RFLAGS constraints (IOPL, IF)                         │ │
│   │   • Segment register validation                                     │ │
│   │   • Stack switching back to user stack                              │ │
│   │                                                                     │ │
│   │   Modern mitigations (Meltdown/Spectre):                            │ │
│   │   • KPTI (Kernel Page Table Isolation) - switch page tables         │ │
│   │   • IBRS/IBPB - indirect branch restrictions                        │ │
│   │   • STIBP - single thread indirect branch predictors                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Linux Kernel Implementation

### Core Data Structures

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX INTERRUPT DATA STRUCTURES                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   STRUCT IRQ_DESC (per-IRQ descriptor):                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Simplified from include/linux/irqdesc.h */                     │ │
│   │   struct irq_desc {                                                 │ │
│   │       struct irq_data         irq_data;      /* IRQ chip data */    │ │
│   │       struct irqaction       *action;        /* Handler chain */    │ │
│   │       unsigned int            status_use_accessors;                 │ │
│   │       unsigned int            depth;         /* Disable depth */    │ │
│   │       unsigned int            irq_count;     /* Interrupt count */  │ │
│   │       unsigned int            irqs_unhandled;                       │ │
│   │       raw_spinlock_t          lock;          /* Descriptor lock */  │ │
│   │       const char             *name;          /* Flow handler name */│ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   Array: irq_desc[NR_IRQS] - one entry per interrupt vector         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   STRUCT IRQACTION (handler registration):                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct irqaction {                                                │ │
│   │       irq_handler_t       handler;     /* Handler function */       │ │
│   │       void               *dev_id;      /* Device identifier */      │ │
│   │       unsigned int        flags;       /* IRQF_* flags */           │ │
│   │       const char         *name;        /* /proc/interrupts name */  │ │
│   │       struct irqaction   *next;        /* Shared IRQ chain */       │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   For shared interrupts: multiple irqaction structs chained         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   STRUCT IRQ_CHIP (hardware abstraction):                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct irq_chip {                                                 │ │
│   │       const char     *name;                                         │ │
│   │       void (*irq_enable)(struct irq_data *data);                    │ │
│   │       void (*irq_disable)(struct irq_data *data);                   │ │
│   │       void (*irq_ack)(struct irq_data *data);                       │ │
│   │       void (*irq_mask)(struct irq_data *data);                      │ │
│   │       void (*irq_unmask)(struct irq_data *data);                    │ │
│   │       void (*irq_eoi)(struct irq_data *data);                       │ │
│   │       int  (*irq_set_affinity)(struct irq_data *data, ...);         │ │
│   │       int  (*irq_set_type)(struct irq_data *data, unsigned int);    │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   Examples: "IO-APIC", "PIC", "MSI", "GICv3" (ARM)                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   RELATIONSHIP DIAGRAM:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   irq_desc[33]                                                      │ │
│   │   ┌─────────────────────┐                                           │ │
│   │   │ irq_data            │──────▶ irq_chip (IO-APIC operations)      │ │
│   │   ├─────────────────────┤                                           │ │
│   │   │ action              │──┐                                        │ │
│   │   ├─────────────────────┤  │    ┌───────────────────┐               │ │
│   │   │ lock                │  └───▶│ irqaction         │               │ │
│   │   ├─────────────────────┤       │ handler: eth0_irq │               │ │
│   │   │ name: "edge"        │       │ dev_id: eth0_dev  │               │ │
│   │   └─────────────────────┘       │ next ─────────────┼──▶ NULL       │ │
│   │                                 └───────────────────┘    (or next   │ │
│   │                                                           handler)  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Requesting and Freeing IRQs

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REQUEST_IRQ / FREE_IRQ API                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   REGISTERING AN INTERRUPT HANDLER:                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int request_irq(                                                  │ │
│   │       unsigned int irq,           /* IRQ number */                  │ │
│   │       irq_handler_t handler,      /* Handler function */            │ │
│   │       unsigned long flags,        /* IRQF_* flags */                │ │
│   │       const char *name,           /* Device name */                 │ │
│   │       void *dev_id                /* Device identifier */           │ │
│   │   );                                                                │ │
│   │                                                                     │ │
│   │   Returns: 0 on success, negative error code on failure             │ │
│   │                                                                     │ │
│   │   /* Example: network driver */                                     │ │
│   │   static irqreturn_t my_interrupt(int irq, void *dev_id)            │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = dev_id;                               │ │
│   │       u32 status = readl(dev->regs + STATUS);                       │ │
│   │                                                                     │ │
│   │       if (!(status & MY_IRQ_PENDING))                               │ │
│   │           return IRQ_NONE;    /* Not our interrupt */               │ │
│   │                                                                     │ │
│   │       /* Handle interrupt */                                        │ │
│   │       writel(status, dev->regs + STATUS);  /* Ack */                │ │
│   │       /* Queue work for bottom half */                              │ │
│   │       napi_schedule(&dev->napi);                                    │ │
│   │                                                                     │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* In probe function */                                           │ │
│   │   ret = request_irq(pdev->irq, my_interrupt,                        │ │
│   │                     IRQF_SHARED, "my_device", dev);                  │ │
│   │   if (ret) {                                                        │ │
│   │       dev_err(&pdev->dev, "Failed to request IRQ\n");               │ │
│   │       return ret;                                                   │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IRQF FLAGS:                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌────────────────────┬──────────────────────────────────────────┐ │ │
│   │   │ Flag               │ Description                              │ │ │
│   │   ├────────────────────┼──────────────────────────────────────────┤ │ │
│   │   │ IRQF_SHARED        │ IRQ can be shared with other devices     │ │ │
│   │   │ IRQF_TRIGGER_HIGH  │ Level-triggered, active high             │ │ │
│   │   │ IRQF_TRIGGER_LOW   │ Level-triggered, active low              │ │ │
│   │   │ IRQF_TRIGGER_RISING│ Edge-triggered, rising edge              │ │ │
│   │   │ IRQF_TRIGGER_FALLING│Edge-triggered, falling edge             │ │ │
│   │   │ IRQF_ONESHOT       │ Keep IRQ disabled until handler done     │ │ │
│   │   │ IRQF_NO_SUSPEND    │ Don't disable during suspend             │ │ │
│   │   │ IRQF_NOBALANCING   │ Exclude from IRQ balancing               │ │ │
│   │   └────────────────────┴──────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   FREEING AN INTERRUPT:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   void free_irq(unsigned int irq, void *dev_id);                    │ │
│   │                                                                     │ │
│   │   /* In remove function */                                          │ │
│   │   free_irq(pdev->irq, dev);   /* dev_id MUST match request_irq */   │ │
│   │                                                                     │ │
│   │   IMPORTANT:                                                        │ │
│   │   • For shared IRQs, dev_id identifies which handler to remove      │ │
│   │   • free_irq() waits for running handlers to complete               │ │
│   │   • Must not call from interrupt context                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   HANDLER RETURN VALUES:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   typedef irqreturn_t (*irq_handler_t)(int, void *);                │ │
│   │                                                                     │ │
│   │   ┌─────────────────┬────────────────────────────────────────────┐  │ │
│   │   │ Return Value    │ Meaning                                    │  │ │
│   │   ├─────────────────┼────────────────────────────────────────────┤  │ │
│   │   │ IRQ_NONE        │ Interrupt was not from this device         │  │ │
│   │   │ IRQ_HANDLED     │ Interrupt was handled successfully         │  │ │
│   │   │ IRQ_WAKE_THREAD │ Handler requests threaded handler to run   │  │ │
│   │   └─────────────────┴────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   For SHARED interrupts: if ALL handlers return IRQ_NONE,           │ │
│   │   kernel logs "spurious interrupt" warning                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Shared Interrupts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SHARED INTERRUPTS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Multiple devices can share a single IRQ line using IRQF_SHARED.          │
│                                                                            │
│   HOW SHARED INTERRUPTS WORK:                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   IRQ Line                                                          │ │
│   │      │                                                              │ │
│   │      ▼                                                              │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │                    do_IRQ(irq)                            │     │ │
│   │   │                         │                                 │     │ │
│   │   │       ┌─────────────────┼─────────────────┐               │     │ │
│   │   │       │                 │                 │               │     │ │
│   │   │       ▼                 ▼                 ▼               │     │ │
│   │   │  handler_A()      handler_B()      handler_C()            │     │ │
│   │   │       │                 │                 │               │     │ │
│   │   │       ▼                 ▼                 ▼               │     │ │
│   │   │  Check device     Check device     Check device           │     │ │
│   │   │  "Is this me?"    "Is this me?"    "Is this me?"          │     │ │
│   │   │       │                 │                 │               │     │ │
│   │   │       ▼                 ▼                 ▼               │     │ │
│   │   │  IRQ_NONE        IRQ_HANDLED       IRQ_NONE               │     │ │
│   │   │  (not mine)      (it was me!)      (not mine)             │     │ │
│   │   │                                                           │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   REQUIREMENTS FOR SHARED INTERRUPTS:                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. All devices must use IRQF_SHARED flag                          │ │
│   │   2. All devices must provide non-NULL dev_id                       │ │
│   │   3. Handlers must be able to identify their device's interrupt     │ │
│   │   4. Level-triggered interrupts work best for sharing               │ │
│   │                                                                     │ │
│   │   /* Handler must check device status */                            │ │
│   │   static irqreturn_t shared_handler(int irq, void *dev_id)          │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = dev_id;                               │ │
│   │                                                                     │ │
│   │       /* CRITICAL: Check if THIS device raised interrupt */         │ │
│   │       if (!(ioread32(dev->status_reg) & IRQ_PENDING))               │ │
│   │           return IRQ_NONE;  /* Not our interrupt */                 │ │
│   │                                                                     │ │
│   │       /* Handle it */                                               │ │
│   │       process_interrupt(dev);                                       │ │
│   │       iowrite32(IRQ_ACK, dev->status_reg);                          │ │
│   │                                                                     │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Software Interrupts and System Calls

### System Call Mechanism

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM CALL MECHANISM                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   System calls are the interface between user programs and the kernel.     │
│   They are implemented using software interrupts or special instructions.  │
│                                                                            │
│   EVOLUTION OF SYSTEM CALL MECHANISMS:                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Era          │ Mechanism          │ Instruction                   │ │
│   │   ─────────────┼────────────────────┼─────────────────────────────  │ │
│   │   Legacy x86   │ Software Interrupt │ int 0x80                      │ │
│   │   Modern x86   │ Fast Syscall       │ sysenter/sysexit (32-bit)     │ │
│   │   x86-64       │ Fast Syscall       │ syscall/sysret (64-bit)       │ │
│   │   ARM          │ Supervisor Call    │ svc (formerly swi)            │ │
│   │   ARM64        │ Supervisor Call    │ svc #0                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LEGACY: INT 0x80 SYSTEM CALL:                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   User Space                    Kernel Space                        │ │
│   │   ──────────                    ────────────                        │ │
│   │                                                                     │ │
│   │   /* User program */            /* Kernel */                        │ │
│   │   mov eax, 4      ; syscall #   system_call:                        │ │
│   │   mov ebx, 1      ; fd (stdout)     push registers                  │ │
│   │   mov ecx, msg    ; buffer          cmp eax, NR_syscalls            │ │
│   │   mov edx, len    ; length          jae invalid                     │ │
│   │   int 0x80        ; TRAP! ──────▶   call sys_call_table[eax]        │ │
│   │                         ◀──────     pop registers                   │ │
│   │   ; continues here                  iret                            │ │
│   │                                                                     │ │
│   │   CPU automatically:                                                │ │
│   │   • Switches from ring 3 to ring 0                                  │ │
│   │   • Loads kernel stack from TSS                                     │ │
│   │   • Saves SS, ESP, EFLAGS, CS, EIP on kernel stack                  │ │
│   │   • Disables interrupts (clears IF)                                 │ │
│   │   • Jumps to IDT[0x80] handler                                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MODERN: SYSCALL/SYSRET (x86-64):                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Much faster than int 0x80 - no IDT lookup, no stack switch!       │ │
│   │                                                                     │ │
│   │   /* User space (libc wrapper) */                                   │ │
│   │   mov rax, __NR_write    ; syscall number                           │ │
│   │   mov rdi, fd            ; arg1                                     │ │
│   │   mov rsi, buf           ; arg2                                     │ │
│   │   mov rdx, count         ; arg3                                     │ │
│   │   syscall                ; FAST TRAP! ─────┐                        │ │
│   │   ; returns here                           │                        │ │
│   │                                            ▼                        │ │
│   │   /* Kernel entry */                                                │ │
│   │   entry_SYSCALL_64:                                                 │ │
│   │       swapgs                    ; Load kernel GS                    │ │
│   │       mov [gs:cpu_tss], rsp     ; Save user RSP                     │ │
│   │       mov rsp, [gs:kernel_stack]; Load kernel RSP                   │ │
│   │       push user_ss                                                  │ │
│   │       push user_rsp                                                 │ │
│   │       push r11                  ; RFLAGS saved in R11               │ │
│   │       push user_cs                                                  │ │
│   │       push rcx                  ; RIP saved in RCX                  │ │
│   │       ... save more registers ...                                   │ │
│   │       call do_syscall_64                                            │ │
│   │                                                                     │ │
│   │   SYSCALL instruction automatically:                                │ │
│   │   • RCX ← RIP (return address)                                      │ │
│   │   • R11 ← RFLAGS                                                    │ │
│   │   • RIP ← IA32_LSTAR MSR (entry point)                              │ │
│   │   • CS ← IA32_STAR MSR bits [47:32]                                 │ │
│   │   • SS ← IA32_STAR MSR bits [47:32] + 8                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### System Call Table

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM CALL TABLE                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE SYSCALL DISPATCH:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* arch/x86/entry/syscall_64.c */                                 │ │
│   │   const sys_call_ptr_t sys_call_table[__NR_syscall_max+1] = {       │ │
│   │       [0]   = sys_read,                                             │ │
│   │       [1]   = sys_write,                                            │ │
│   │       [2]   = sys_open,                                             │ │
│   │       [3]   = sys_close,                                            │ │
│   │       ...                                                           │ │
│   │       [60]  = sys_exit,                                             │ │
│   │       ...                                                           │ │
│   │       [435] = sys_clone3,        /* Recent addition */              │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   /* Dispatch logic */                                              │ │
│   │   __visible void do_syscall_64(struct pt_regs *regs)                │ │
│   │   {                                                                 │ │
│   │       unsigned long nr = regs->ax;                                  │ │
│   │                                                                     │ │
│   │       if (likely(nr < NR_syscalls)) {                               │ │
│   │           regs->ax = sys_call_table[nr](regs);                      │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMMON SYSTEM CALLS:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌────────┬────────────────┬──────────────────────────────────┐    │ │
│   │   │ Number │ Name           │ Description                      │    │ │
│   │   ├────────┼────────────────┼──────────────────────────────────┤    │ │
│   │   │ 0      │ read           │ Read from file descriptor        │    │ │
│   │   │ 1      │ write          │ Write to file descriptor         │    │ │
│   │   │ 2      │ open           │ Open file                        │    │ │
│   │   │ 3      │ close          │ Close file descriptor            │    │ │
│   │   │ 9      │ mmap           │ Map memory                       │    │ │
│   │   │ 57     │ fork           │ Create child process             │    │ │
│   │   │ 59     │ execve         │ Execute program                  │    │ │
│   │   │ 60     │ exit           │ Terminate process                │    │ │
│   │   │ 62     │ kill           │ Send signal                      │    │ │
│   │   │ 231    │ exit_group     │ Exit all threads                 │    │ │
│   │   └────────┴────────────────┴──────────────────────────────────┘    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Exceptions: Page Faults

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE FAULT HANDLING                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Page faults (exception #14) are synchronous interrupts triggered when    │
│   accessing memory that isn't currently mapped or has wrong permissions.   │
│                                                                            │
│   PAGE FAULT CAUSES:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. Page not present     - Page swapped out or never allocated     │ │
│   │   2. Permission violation - Write to read-only, exec non-exec       │ │
│   │   3. Copy-on-write        - Write to shared page after fork()       │ │
│   │   4. Stack growth         - Access below current stack              │ │
│   │   5. Invalid access       - Bug in program (SIGSEGV)                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PAGE FAULT FLOW:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   mov rax, [rbx]    ; Access memory at address in RBX               │ │
│   │         │                                                           │ │
│   │         ▼                                                           │ │
│   │   ┌─────────────┐                                                   │ │
│   │   │ MMU checks  │                                                   │ │
│   │   │ page table  │                                                   │ │
│   │   └──────┬──────┘                                                   │ │
│   │          │ Page not present or permission denied                    │ │
│   │          ▼                                                          │ │
│   │   ┌─────────────────────────────────────────────┐                   │ │
│   │   │         CPU EXCEPTION #14                   │                   │ │
│   │   │ • Push error code (P,W/R,U/S,RSVD,I/D)      │                   │ │
│   │   │ • CR2 ← faulting address                    │                   │ │
│   │   │ • Jump to page_fault handler                │                   │ │
│   │   └──────────────────┬──────────────────────────┘                   │ │
│   │                      ▼                                              │ │
│   │   ┌─────────────────────────────────────────────┐                   │ │
│   │   │         do_page_fault()                     │                   │ │
│   │   │ 1. Read CR2 (faulting address)              │                   │ │
│   │   │ 2. Find VMA for address                     │                   │ │
│   │   │ 3. Check permissions                        │                   │ │
│   │   │ 4. Handle based on fault type               │                   │ │
│   │   └──────────────────┬──────────────────────────┘                   │ │
│   │                      │                                              │ │
│   │          ┌───────────┼───────────┐                                  │ │
│   │          ▼           ▼           ▼                                  │ │
│   │     Valid fault  COW fault   Invalid fault                          │ │
│   │          │           │           │                                  │ │
│   │          ▼           ▼           ▼                                  │ │
│   │     Allocate     Copy page   Send SIGSEGV                           │ │
│   │     page, map    to new      to process                             │ │
│   │          │       page            │                                  │ │
│   │          │           │           │                                  │ │
│   │          └─────┬─────┘           │                                  │ │
│   │                ▼                 ▼                                  │ │
│   │           Return and        Process killed                          │ │
│   │           retry access      (or handles signal)                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ERROR CODE BITS (pushed on stack):                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Bit 0 (P):    0 = page not present, 1 = protection violation      │ │
│   │   Bit 1 (W/R):  0 = read access, 1 = write access                   │ │
│   │   Bit 2 (U/S):  0 = supervisor mode, 1 = user mode                  │ │
│   │   Bit 3 (RSVD): 1 = reserved bit violation in page table            │ │
│   │   Bit 4 (I/D):  1 = instruction fetch (NX violation)                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 8. Interrupt Context vs Process Context

```
┌───────────────────────────────────────────────────────────────────────────┐
│                INTERRUPT CONTEXT vs PROCESS CONTEXT                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The kernel runs in two fundamentally different contexts, each with       │
│   different rules about what operations are allowed.                       │
│                                                                            │
│   CONTEXT COMPARISON:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌──────────────────────────┬──────────────────────────────────┐   │ │
│   │   │    PROCESS CONTEXT       │    INTERRUPT CONTEXT             │   │ │
│   │   ├──────────────────────────┼──────────────────────────────────┤   │ │
│   │   │ • Has a "current" task   │ • No meaningful "current"        │   │ │
│   │   │ • Can sleep/block        │ • CANNOT sleep or block          │   │ │
│   │   │ • Can access user memory │ • Cannot access user memory      │   │ │
│   │   │ • Preemptible (usually)  │ • Not preemptible                │   │ │
│   │   │ • Uses process's stack   │ • Uses dedicated IRQ stack       │   │ │
│   │   │ • Can hold mutexes       │ • Spinlocks only                 │   │ │
│   │   │ • Entered via syscall    │ • Entered via hardware IRQ       │   │ │
│   │   └──────────────────────────┴──────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY CAN'T INTERRUPT HANDLERS SLEEP?                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. NO PROCESS TO RESCHEDULE                                       │ │
│   │      • Interrupt can occur during ANY process                       │ │
│   │      • "current" is whatever process was interrupted                │ │
│   │      • Sleeping would put the WRONG process to sleep!               │ │
│   │                                                                     │ │
│   │   2. DEADLOCK RISK                                                  │ │
│   │      • Process A holds lock, gets interrupted                       │ │
│   │      • Handler tries to acquire same lock                           │ │
│   │      • Handler blocks, but A can't run to release lock              │ │
│   │      • DEADLOCK!                                                    │ │
│   │                                                                     │ │
│   │   3. LATENCY                                                        │ │
│   │      • Interrupts should complete QUICKLY                           │ │
│   │      • Sleeping handler blocks all other interrupts                 │ │
│   │      • System becomes unresponsive                                  │ │
│   │                                                                     │ │
│   │   /* THIS IS WRONG - will crash or deadlock! */                     │ │
│   │   static irqreturn_t bad_handler(int irq, void *dev_id)             │ │
│   │   {                                                                 │ │
│   │       void *p = kmalloc(1024, GFP_KERNEL);  /* May sleep! */        │ │
│   │       mutex_lock(&my_mutex);                /* May sleep! */        │ │
│   │       copy_from_user(...);                  /* May fault/sleep */   │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* THIS IS CORRECT */                                             │ │
│   │   static irqreturn_t good_handler(int irq, void *dev_id)            │ │
│   │   {                                                                 │ │
│   │       void *p = kmalloc(1024, GFP_ATOMIC);  /* Never sleeps */      │ │
│   │       spin_lock(&my_spinlock);              /* Never sleeps */      │ │
│   │       /* Cannot access user memory at all */                        │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DETECTING CONTEXT:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Kernel provides helper functions */                            │ │
│   │                                                                     │ │
│   │   in_interrupt()     - True if in ANY interrupt context             │ │
│   │   in_irq()           - True if in hardware IRQ handler              │ │
│   │   in_softirq()       - True if in softirq context                   │ │
│   │   in_task()          - True if in process context                   │ │
│   │   in_atomic()        - True if sleeping not allowed                 │ │
│   │                                                                     │ │
│   │   /* Example: function that works in both contexts */               │ │
│   │   void my_function(void)                                            │ │
│   │   {                                                                 │ │
│   │       if (in_interrupt()) {                                         │ │
│   │           spin_lock(&lock);        /* Interrupt context */          │ │
│   │           do_work_atomic();                                         │ │
│   │           spin_unlock(&lock);                                       │ │
│   │       } else {                                                      │ │
│   │           mutex_lock(&mutex);      /* Process context */            │ │
│   │           do_work_sleepable();                                      │ │
│   │           mutex_unlock(&mutex);                                     │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   INTERRUPT STACKS:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Each CPU has dedicated interrupt stacks to prevent stack overflow │ │
│   │   from nested interrupts eating into the process kernel stack.      │ │
│   │                                                                     │ │
│   │   Per-CPU Stacks (x86-64):                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   CPU 0                CPU 1              CPU N             │   │ │
│   │   │   ┌──────────┐        ┌──────────┐       ┌──────────┐       │   │ │
│   │   │   │ IRQ Stack│        │ IRQ Stack│       │ IRQ Stack│       │   │ │
│   │   │   │ (16 KB)  │        │ (16 KB)  │       │ (16 KB)  │       │   │ │
│   │   │   ├──────────┤        ├──────────┤       ├──────────┤       │   │ │
│   │   │   │ NMI Stack│        │ NMI Stack│       │ NMI Stack│       │   │ │
│   │   │   │ (16 KB)  │        │ (16 KB)  │       │ (16 KB)  │       │   │ │
│   │   │   ├──────────┤        ├──────────┤       ├──────────┤       │   │ │
│   │   │   │DF Stack  │        │DF Stack  │       │DF Stack  │       │   │ │
│   │   │   │(Dbl Flt) │        │(Dbl Flt) │       │(Dbl Flt) │       │   │ │
│   │   │   └──────────┘        └──────────┘       └──────────┘       │   │ │
│   │   │                                                             │   │ │
│   │   │   IST (Interrupt Stack Table) in TSS specifies which stack  │   │ │
│   │   │   to use for each exception type.                           │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Deferred Work Mechanisms

### Top Half vs Bottom Half

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TOP HALF vs BOTTOM HALF                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Interrupt handling is split into two parts to minimize time spent        │
│   with interrupts disabled while still handling all necessary work.        │
│                                                                            │
│   THE PROBLEM:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Network packet arrives:                                           │ │
│   │   • Copy data from hardware buffer (MUST do immediately)            │ │
│   │   • Parse headers                    (can do later)                 │ │
│   │   • Route packet                     (can do later)                 │ │
│   │   • Deliver to socket                (can do later)                 │ │
│   │   • Wake up waiting process          (can do later)                 │ │
│   │                                                                     │ │
│   │   If we do ALL this with interrupts disabled:                       │ │
│   │   • Other interrupts are lost                                       │ │
│   │   • System latency suffers                                          │ │
│   │   • Hardware buffers overflow                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE SOLUTION: TWO-PART HANDLING                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │         IRQ                                                         │ │
│   │          │                                                          │ │
│   │          ▼                                                          │ │
│   │   ┌──────────────────────────────────────────────────────┐          │ │
│   │   │               TOP HALF (Hardirq)                     │          │ │
│   │   │                                                      │          │ │
│   │   │   • Runs with interrupts disabled                    │          │ │
│   │   │   • Acknowledge hardware interrupt                   │          │ │
│   │   │   • Copy data from hardware                          │          │ │
│   │   │   • Schedule bottom half                             │          │ │
│   │   │   • Return QUICKLY                                   │          │ │
│   │   │                                                      │          │ │
│   │   │   Time: microseconds                                 │          │ │
│   │   └─────────────────────┬────────────────────────────────┘          │ │
│   │                         │ schedule                                  │ │
│   │                         ▼                                           │ │
│   │   ┌──────────────────────────────────────────────────────┐          │ │
│   │   │               BOTTOM HALF (Softirq)                  │          │ │
│   │   │                                                      │          │ │
│   │   │   • Runs with interrupts enabled                     │          │ │
│   │   │   • Can be preempted by new hardirqs                 │          │ │
│   │   │   • Process data                                     │          │ │
│   │   │   • Deliver to higher layers                         │          │ │
│   │   │   • Can take longer                                  │          │ │
│   │   │                                                      │          │ │
│   │   │   Time: milliseconds                                 │          │ │
│   │   └──────────────────────────────────────────────────────┘          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Understanding Deferred Work - From Basics

This section explains deferred work mechanisms from the ground up, using
analogies and step-by-step examples for those new to kernel concepts.

#### Part 1: What is an Interrupt?

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNDERSTANDING INTERRUPTS - BASICS                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Think of your CPU as a chef cooking in a kitchen:                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         THE CPU (Chef)                              │ │
│   │                                                                     │ │
│   │    The chef is cooking a meal (running your program)                │ │
│   │                                                                     │ │
│   │         🧑‍🍳 ← Currently chopping vegetables                          │ │
│   │              (executing instructions)                               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Now, suddenly the doorbell rings (hardware interrupt):                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │    🔔 DING DONG! (Interrupt from keyboard/mouse/network)            │ │
│   │                                                                     │ │
│   │    The chef MUST stop what they're doing and answer the door        │ │
│   │                                                                     │ │
│   │         🧑‍🍳 → 🚪                                                      │ │
│   │         Chef stops cooking, goes to door                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   An interrupt is a signal from hardware saying:                           │
│   "HEY! Something happened! Deal with me NOW!"                             │
│                                                                            │
│   Examples of interrupts:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • You pressed a key on keyboard                                    │ │
│   │  • Mouse moved                                                      │ │
│   │  • Network card received data                                       │ │
│   │  • Disk finished reading data                                       │ │
│   │  • Timer ticked                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 2: The Core Problem

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE PROBLEM WITH INTERRUPTS                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Critical issue: While handling an interrupt, other interrupts            │
│   are BLOCKED.                                                             │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  TIME ──────────────────────────────────────────────────────────▶   │ │
│   │                                                                     │ │
│   │  Interrupt      ████████████████████████████████                    │ │
│   │  Handler        ▲                              ▲                    │ │
│   │  Running        │   Takes 1 millisecond        │                    │ │
│   │                 │                              │                    │ │
│   │  Other          │  ❌ BLOCKED! ❌               │                    │ │
│   │  Interrupts     │  🔔 keyboard?  IGNORED       │                    │ │
│   │                 │  🔔 network?   IGNORED       │                    │ │
│   │                 │  🔔 timer?     IGNORED       │                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   REAL-WORLD ANALOGY: The Emergency Room                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   BAD APPROACH (No splitting):                                      │ │
│   │   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━        │ │
│   │                                                                     │ │
│   │   Patient A arrives (car accident) 🚑                               │ │
│   │                                                                     │ │
│   │   Doctor does EVERYTHING for Patient A:                             │ │
│   │   ├── Check vital signs (2 min)        ← MUST do immediately        │ │
│   │   ├── Stop bleeding (5 min)            ← MUST do immediately        │ │
│   │   ├── Take X-rays (15 min)             ← Can wait                   │ │
│   │   ├── Fill paperwork (10 min)          ← Can wait                   │ │
│   │   ├── Call insurance (20 min)          ← Can wait                   │ │
│   │   └── Update medical records (10 min)  ← Can wait                   │ │
│   │                                                                     │ │
│   │       TOTAL: 62 minutes                                             │ │
│   │                                                                     │ │
│   │   Meanwhile: Patient B (heart attack) arrives at minute 5           │ │
│   │              Patient B WAITS 57 minutes! 💀                         │ │
│   │                                                                     │ │
│   │   This is TERRIBLE! Patient B could die!                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 3: The Solution - Split the Work

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE SOLUTION: SPLIT THE WORK                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   GOOD APPROACH (Split into Top Half + Bottom Half):                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Patient A arrives (car accident) 🚑                               │ │
│   │                                                                     │ │
│   │   TOP HALF - Doctor does only CRITICAL things:                      │ │
│   │   ├── Check vital signs (2 min)        ✓ DONE                       │ │
│   │   ├── Stop bleeding (5 min)            ✓ DONE                       │ │
│   │   └── Write note: "needs X-ray, paperwork, etc."                    │ │
│   │                                                                     │ │
│   │       TOTAL: 7 minutes, then doctor is FREE                         │ │
│   │                                                                     │ │
│   │   At minute 5: Patient B (heart attack) arrives                     │ │
│   │                Doctor can help Patient B immediately! ✓             │ │
│   │                                                                     │ │
│   │   BOTTOM HALF - Nurses/assistants handle rest LATER:                │ │
│   │   ├── Take X-rays                                                   │ │
│   │   ├── Fill paperwork                                                │ │
│   │   ├── Call insurance                                                │ │
│   │   └── Update records                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   This is EXACTLY what Linux does with interrupts!                         │
│                                                                            │
│   TOP HALF vs BOTTOM HALF IN LINUX:                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │                      TOP HALF                                       │ │
│   │                   (Interrupt Handler)                               │ │
│   │               ════════════════════════                              │ │
│   │                                                                     │ │
│   │   When:     Runs IMMEDIATELY when interrupt occurs                  │ │
│   │   Context:  Interrupts are DISABLED (no other interrupts)           │ │
│   │   Time:     MUST be VERY FAST (microseconds)                        │ │
│   │   Can do:   Only critical, time-sensitive work                      │ │
│   │   Cannot:   Sleep, wait, allocate memory, take locks                │ │
│   │                                                                     │ │
│   │   Tasks:                                                            │ │
│   │   ✓ Acknowledge hardware ("I got your signal")                      │ │
│   │   ✓ Copy data from hardware buffer (before it's lost)               │ │
│   │   ✓ Schedule the bottom half ("do the rest later")                  │ │
│   │   ✓ EXIT QUICKLY!                                                   │ │
│   │                                                                     │ │
│   │                          │                                          │ │
│   │                          │ "I'll handle the rest later"             │ │
│   │                          ▼                                          │ │
│   │                                                                     │ │
│   │                     BOTTOM HALF                                     │ │
│   │              (Softirq / Tasklet / Workqueue)                        │ │
│   │               ════════════════════════════                          │ │
│   │                                                                     │ │
│   │   When:     Runs LATER (when convenient)                            │ │
│   │   Context:  Interrupts are ENABLED (others can interrupt)           │ │
│   │   Time:     Can take longer                                         │ │
│   │   Can do:   Most of the actual processing work                      │ │
│   │                                                                     │ │
│   │   Tasks:                                                            │ │
│   │   ✓ Process the data (parse, validate, transform)                   │ │
│   │   ✓ Update data structures                                          │ │
│   │   ✓ Deliver data to applications                                    │ │
│   │   ✓ Wake up waiting processes                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 4: Concrete Example - Network Packet

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EXAMPLE: NETWORK PACKET ARRIVES                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Let's trace exactly what happens when your computer receives             │
│   a network packet:                                                        │
│                                                                            │
│   STEP 1: Packet arrives at Network Card (NIC)                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │    Internet                           Your Computer                 │ │
│   │        │                                   │                        │ │
│   │        │  📦 Packet                        │                        │ │
│   │        │  ════════                         │                        │ │
│   │        │  │ Data │ ──────────────────────▶ │ Network Card (NIC)     │ │
│   │        │  ════════                         │                        │ │
│   │                                            │ NIC has small buffer   │ │
│   │                                            │ ┌──────────┐           │ │
│   │                                            │ │📦 packet │           │ │
│   │                                            │ └──────────┘           │ │
│   │                                            │                        │ │
│   │                                            │ NIC sends INTERRUPT    │ │
│   │                                            │ to CPU: "Hey! Data!"   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   STEP 2: TOP HALF runs (Interrupt Handler)                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ⚡ INTERRUPTS DISABLED - Must be FAST!                            │ │
│   │                                                                     │ │
│   │   CPU was doing:  Running Firefox browser                           │ │
│   │                        │                                            │ │
│   │                        ▼ INTERRUPT!                                 │ │
│   │                                                                     │ │
│   │   CPU now does:   [TOP HALF - ~10 microseconds]                     │ │
│   │                   │                                                 │ │
│   │                   ├── 1. "Hey NIC, I got your interrupt" (ACK)      │ │
│   │                   │                                                 │ │
│   │                   ├── 2. Copy packet from NIC buffer to RAM         │ │
│   │                   │      (NIC buffer is tiny, might overflow!)      │ │
│   │                   │                                                 │ │
│   │                   │      NIC buffer          RAM                    │ │
│   │                   │      ┌────────┐         ┌────────────┐          │ │
│   │                   │      │📦      │ ──────▶ │ 📦 safe!   │          │ │
│   │                   │      └────────┘         └────────────┘          │ │
│   │                   │                                                 │ │
│   │                   ├── 3. Tell NIC: "Don't interrupt me again,       │ │
│   │                   │                 I'll poll you instead"          │ │
│   │                   │                                                 │ │
│   │                   └── 4. Schedule bottom half: "Process this later" │ │
│   │                                                                     │ │
│   │   CPU returns to: Firefox browser (interrupts enabled again)        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   STEP 3: BOTTOM HALF runs (Later, when convenient)                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✓ INTERRUPTS ENABLED - Can take time, others can interrupt        │ │
│   │                                                                     │ │
│   │   CPU does:   [BOTTOM HALF - ~100+ microseconds]                    │ │
│   │               │                                                     │ │
│   │               ├── 1. Look at packet in RAM                          │ │
│   │               │      ┌─────────────────────────────────────┐        │ │
│   │               │      │ Ethernet │  IP   │  TCP  │  HTTP   │        │ │
│   │               │      │  Header  │Header │Header │  Data   │        │ │
│   │               │      └─────────────────────────────────────┘        │ │
│   │               │                                                     │ │
│   │               ├── 2. Parse Ethernet header                          │ │
│   │               │      "This is for my MAC address ✓"                 │ │
│   │               │                                                     │ │
│   │               ├── 3. Parse IP header                                │ │
│   │               │      "Source: 142.250.185.78 (google.com)"          │ │
│   │               │      "Destination: 192.168.1.100 (me)"              │ │
│   │               │                                                     │ │
│   │               ├── 4. Parse TCP header                               │ │
│   │               │      "This is for port 443 (HTTPS)"                 │ │
│   │               │      "Sequence number: 12345"                       │ │
│   │               │                                                     │ │
│   │               ├── 5. Find the socket (Firefox's connection)         │ │
│   │               │      "Firefox is waiting for this!"                 │ │
│   │               │                                                     │ │
│   │               ├── 6. Put data in socket's receive buffer            │ │
│   │               │      Socket buffer: [....📦 new data....]           │ │
│   │               │                                                     │ │
│   │               └── 7. Wake up Firefox                                │ │
│   │                      "Hey Firefox, your data is ready!"             │ │
│   │                                                                     │ │
│   │                      Firefox: read() returns with data!             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 5: The Three Bottom Half Mechanisms

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THREE WAYS TO DO DEFERRED WORK                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Linux provides THREE different ways to do bottom half work.              │
│   Think of them as three different types of assistants:                    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │ │
│   │    │  SOFTIRQ    │   │  TASKLET    │   │ WORKQUEUE   │              │ │
│   │    │             │   │             │   │             │              │ │
│   │    │  Fastest    │   │  Medium     │   │  Flexible   │              │ │
│   │    │  Complex    │   │  Simple     │   │  Can Sleep  │              │ │
│   │    │             │   │             │   │             │              │ │
│   │    │  🏎️ Race    │   │  🚗 Car     │   │  🚌 Bus     │              │ │
│   │    │    Car      │   │             │   │             │              │ │
│   │    └─────────────┘   └─────────────┘   └─────────────┘              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MECHANISM 1: SOFTIRQ (The Race Car 🏎️)                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ANALOGY: Formula 1 Race Car                                       │ │
│   │                                                                     │ │
│   │   • Extremely FAST                                                  │ │
│   │   • Requires expert driver (kernel developers only)                 │ │
│   │   • Fixed number of cars (can't add new ones easily)                │ │
│   │   • Multiple cars can race simultaneously (parallel CPUs)           │ │
│   │                                                                     │ │
│   │   CHARACTERISTICS:                                                  │ │
│   │   ───────────────                                                   │ │
│   │   • Only 10 softirqs exist (hardcoded in kernel)                    │ │
│   │   • Same softirq can run on MULTIPLE CPUs at same time              │ │
│   │   • Cannot sleep (no waiting, no blocking)                          │ │
│   │   • Used for: networking, block devices, timers                     │ │
│   │                                                                     │ │
│   │   SOFTIRQ CONCURRENCY:                                              │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │  CPU 0        CPU 1        CPU 2        CPU 3               │   │ │
│   │   │  ─────        ─────        ─────        ─────               │   │ │
│   │   │    │            │            │            │                 │   │ │
│   │   │    ▼            ▼            ▼            ▼                 │   │ │
│   │   │ ┌───────┐  ┌───────┐   ┌───────┐   ┌───────┐               │   │ │
│   │   │ │NET_RX │  │NET_RX │   │NET_RX │   │NET_RX │               │   │ │
│   │   │ │SOFTIRQ│  │SOFTIRQ│   │SOFTIRQ│   │SOFTIRQ│               │   │ │
│   │   │ └───────┘  └───────┘   └───────┘   └───────┘               │   │ │
│   │   │                                                             │   │ │
│   │   │   ALL RUNNING AT THE SAME TIME!                             │   │ │
│   │   │   (This is why softirqs are fast but complex)               │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MECHANISM 2: TASKLET (The Car 🚗)                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ANALOGY: Regular Car                                              │ │
│   │                                                                     │ │
│   │   • Pretty fast, not as fast as race car                            │ │
│   │   • Regular driver can use (device driver developers)               │ │
│   │   • Can create as many as you want                                  │ │
│   │   • Only ONE instance drives at a time (no parallel copies)         │ │
│   │                                                                     │ │
│   │   CHARACTERISTICS:                                                  │ │
│   │   ───────────────                                                   │ │
│   │   • Built ON TOP of softirqs (uses TASKLET_SOFTIRQ)                 │ │
│   │   • Same tasklet NEVER runs on two CPUs simultaneously              │ │
│   │   • Cannot sleep (still in interrupt context)                       │ │
│   │   • Good for device drivers                                         │ │
│   │                                                                     │ │
│   │   THE KEY GUARANTEE:                                                │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   CPU 0             CPU 1              CPU 2                │   │ │
│   │   │   ─────             ─────              ─────                │   │ │
│   │   │     │                 │                  │                  │   │ │
│   │   │     ▼                 │                  │                  │   │ │
│   │   │ ┌────────┐            ▼                  │                  │   │ │
│   │   │ │ my_    │       (waiting)               │                  │   │ │
│   │   │ │tasklet │            │                  ▼                  │   │ │
│   │   │ │running │            │             (waiting)               │   │ │
│   │   │ └────────┘            │                  │                  │   │ │
│   │   │     │                 │                  │                  │   │ │
│   │   │     ▼ done            ▼                  │                  │   │ │
│   │   │                  ┌────────┐              │                  │   │ │
│   │   │                  │ my_    │              ▼                  │   │ │
│   │   │                  │tasklet │         (waiting)               │   │ │
│   │   │                  │running │              │                  │   │ │
│   │   │                  └────────┘              │                  │   │ │
│   │   │                       │                  │                  │   │ │
│   │   │                       ▼ done             ▼                  │   │ │
│   │   │                                     ┌────────┐              │   │ │
│   │   │                                     │ my_    │              │   │ │
│   │   │                                     │tasklet │              │   │ │
│   │   │                                     │running │              │   │ │
│   │   │                                     └────────┘              │   │ │
│   │   │                                                             │   │ │
│   │   │   The SAME tasklet runs one at a time only!                 │   │ │
│   │   │   This makes programming MUCH easier.                       │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MECHANISM 3: WORKQUEUE (The Bus 🚌)                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ANALOGY: City Bus                                                 │ │
│   │                                                                     │ │
│   │   • Not the fastest, but very flexible                              │ │
│   │   • Can pick up passengers anytime (can sleep!)                     │ │
│   │   • Follows a schedule (managed by kernel)                          │ │
│   │   • Most comfortable ride                                           │ │
│   │                                                                     │ │
│   │   THE BIG DIFFERENCE: WORKQUEUES CAN SLEEP!                         │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   ┌─────────────────┬──────────────────────────────────┐    │   │ │
│   │   │   │ Softirq/Tasklet │ Workqueue                        │    │   │ │
│   │   │   ├─────────────────┼──────────────────────────────────┤    │   │ │
│   │   │   │ Cannot sleep    │ CAN SLEEP! ✓                     │    │   │ │
│   │   │   │ Cannot wait     │ Can wait for locks               │    │   │ │
│   │   │   │ Cannot block    │ Can block on I/O                 │    │   │ │
│   │   │   │ No allocations  │ Can allocate memory              │    │   │ │
│   │   │   │ No mutexes      │ Can use mutexes                  │    │   │ │
│   │   │   └─────────────────┴──────────────────────────────────┘    │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   HOW IT WORKS:                                                     │ │
│   │   ─────────────                                                     │ │
│   │                                                                     │ │
│   │   Linux has kernel threads called "kworker":                        │ │
│   │                                                                     │ │
│   │     $ ps aux | grep kworker                                         │ │
│   │     root    [kworker/0:0]    ← worker for CPU 0                     │ │
│   │     root    [kworker/1:0]    ← worker for CPU 1                     │ │
│   │     root    [kworker/2:0]    ← worker for CPU 2                     │ │
│   │     root    [kworker/u8:0]   ← unbound worker                       │ │
│   │     ...                                                             │ │
│   │                                                                     │ │
│   │   These worker threads pick up "work items" and execute them:       │ │
│   │                                                                     │ │
│   │     Workqueue                    kworker thread                     │ │
│   │     ─────────                    ──────────────                     │ │
│   │     ┌──────────┐                                                    │ │
│   │     │ Work 1   │ ◄──────────────┐                                   │ │
│   │     ├──────────┤                │                                   │ │
│   │     │ Work 2   │                │  kworker picks up                 │ │
│   │     ├──────────┤                │  work items and                   │ │
│   │     │ Work 3   │                │  executes them                    │ │
│   │     ├──────────┤                │                                   │ │
│   │     │   ...    │                │                                   │ │
│   │     └──────────┘                ▼                                   │ │
│   │                          ┌─────────────┐                            │ │
│   │                          │  kworker/0  │                            │ │
│   │                          │             │                            │ │
│   │                          │ Running     │                            │ │
│   │                          │  Work 1     │                            │ │
│   │                          │             │                            │ │
│   │                          │ (can sleep, │                            │ │
│   │                          │  can block, │                            │ │
│   │                          │  can wait)  │                            │ │
│   │                          └─────────────┘                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 6: Code Examples

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CODE EXAMPLES FOR EACH MECHANISM                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TASKLET EXAMPLE:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Step 1: Define what the tasklet will do */                     │ │
│   │   void my_tasklet_function(struct tasklet_struct *t)                │ │
│   │   {                                                                 │ │
│   │       /* This code runs LATER, in bottom half */                    │ │
│   │       /* Process your data here */                                  │ │
│   │       printk("Tasklet is processing data!\n");                      │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* Step 2: Create the tasklet */                                  │ │
│   │   DECLARE_TASKLET(my_tasklet, my_tasklet_function);                 │ │
│   │                                                                     │ │
│   │   /* Step 3: In your interrupt handler (top half), schedule it */   │ │
│   │   irqreturn_t my_interrupt_handler(int irq, void *dev)              │ │
│   │   {                                                                 │ │
│   │       /* Quick! Save the data from hardware */                      │ │
│   │       save_data_from_hardware();                                    │ │
│   │                                                                     │ │
│   │       /* Schedule tasklet to process it later */                    │ │
│   │       tasklet_schedule(&my_tasklet);  /* ← "Do the rest later!" */  │ │
│   │                                                                     │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WORKQUEUE EXAMPLE:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Step 1: Define what the work will do */                        │ │
│   │   void my_work_function(struct work_struct *work)                   │ │
│   │   {                                                                 │ │
│   │       /* This runs in PROCESS CONTEXT */                            │ │
│   │       /* Can do ANYTHING a normal kernel function can do! */        │ │
│   │                                                                     │ │
│   │       void *buffer;                                                 │ │
│   │                                                                     │ │
│   │       /* Can sleep - allocate memory */                             │ │
│   │       buffer = kmalloc(4096, GFP_KERNEL);  /* ← Might sleep! */     │ │
│   │                                                                     │ │
│   │       /* Can sleep - acquire mutex */                               │ │
│   │       mutex_lock(&my_mutex);               /* ← Might sleep! */     │ │
│   │                                                                     │ │
│   │       /* Can sleep - read from disk */                              │ │
│   │       read_data_from_disk(buffer);         /* ← Might sleep! */     │ │
│   │                                                                     │ │
│   │       /* Process the data */                                        │ │
│   │       process_data(buffer);                                         │ │
│   │                                                                     │ │
│   │       mutex_unlock(&my_mutex);                                      │ │
│   │       kfree(buffer);                                                │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* Step 2: Create the work item */                                │ │
│   │   DECLARE_WORK(my_work, my_work_function);                          │ │
│   │                                                                     │ │
│   │   /* Step 3: In your interrupt handler, schedule the work */        │ │
│   │   irqreturn_t my_interrupt_handler(int irq, void *dev)              │ │
│   │   {                                                                 │ │
│   │       /* Quick! Note what happened */                               │ │
│   │       record_interrupt_info();                                      │ │
│   │                                                                     │ │
│   │       /* Schedule work to handle it later */                        │ │
│   │       schedule_work(&my_work);  /* ← "Handle in process context!" */│ │
│   │                                                                     │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 7: Complete Comparison Table

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE COMPARISON OF ALL THREE                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌──────────────┬──────────────┬──────────────┬────────────────────────┐ │
│   │  Feature     │  SOFTIRQ     │  TASKLET     │  WORKQUEUE             │ │
│   ├──────────────┼──────────────┼──────────────┼────────────────────────┤ │
│   │  Speed       │  Fastest 🏎️  │  Fast 🚗     │  Slower 🚌             │ │
│   ├──────────────┼──────────────┼──────────────┼────────────────────────┤ │
│   │  Can Sleep?  │  ❌ NO       │  ❌ NO       │  ✅ YES                │ │
│   ├──────────────┼──────────────┼──────────────┼────────────────────────┤ │
│   │  Runs on     │  Multiple    │  One CPU     │  Worker thread         │ │
│   │  multiple    │  CPUs at     │  at a time   │  (process context)     │ │
│   │  CPUs?       │  once        │              │                        │ │
│   ├──────────────┼──────────────┼──────────────┼────────────────────────┤ │
│   │  Complexity  │  Complex     │  Medium      │  Easy                  │ │
│   │              │  (handle     │  (serialized │  (normal programming)  │ │
│   │              │  concurrency)│  for you)    │                        │ │
│   ├──────────────┼──────────────┼──────────────┼────────────────────────┤ │
│   │  Who uses?   │  Core kernel │  Device      │  Drivers that need     │ │
│   │              │  (networking,│  drivers     │  to sleep/block        │ │
│   │              │  block I/O)  │              │                        │ │
│   ├──────────────┼──────────────┼──────────────┼────────────────────────┤ │
│   │  Can alloc   │  Only with   │  Only with   │  ✅ YES                │ │
│   │  memory?     │  GFP_ATOMIC  │  GFP_ATOMIC  │  (normal GFP_KERNEL)   │ │
│   ├──────────────┼──────────────┼──────────────┼────────────────────────┤ │
│   │  Can use     │  ❌ NO       │  ❌ NO       │  ✅ YES                │ │
│   │  mutex?      │  (spinlock   │  (spinlock   │                        │ │
│   │              │  only)       │  only)       │                        │ │
│   └──────────────┴──────────────┴──────────────┴────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 8: Decision Flowchart

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DECISION FLOWCHART: WHICH TO USE?                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                   ┌─────────────────────┐                                  │
│                   │ Do you need to do   │                                  │
│                   │ deferred work?      │                                  │
│                   └──────────┬──────────┘                                  │
│                              │                                             │
│                              ▼                                             │
│                   ┌─────────────────────┐                                  │
│                   │ Does your work need │                                  │
│                   │ to SLEEP?           │                                  │
│                   └──────────┬──────────┘                                  │
│                              │                                             │
│               ┌──────────────┴──────────────┐                              │
│               │                             │                              │
│               ▼ YES                         ▼ NO                           │
│     ┌─────────────────┐           ┌─────────────────────┐                  │
│     │                 │           │ Is performance      │                  │
│     │  Use WORKQUEUE  │           │ CRITICAL?           │                  │
│     │  🚌             │           │ (millions/second)   │                  │
│     │                 │           └──────────┬──────────┘                  │
│     └─────────────────┘                      │                             │
│                               ┌──────────────┴──────────────┐              │
│                               │                             │              │
│                               ▼ YES                         ▼ NO           │
│                     ┌─────────────────┐           ┌─────────────────┐      │
│                     │ Are you a core  │           │                 │      │
│                     │ kernel developer│           │  Use TASKLET    │      │
│                     │ (networking,    │           │  🚗             │      │
│                     │  block I/O)?    │           │                 │      │
│                     └────────┬────────┘           └─────────────────┘      │
│                              │                                             │
│               ┌──────────────┴──────────────┐                              │
│               │                             │                              │
│               ▼ YES                         ▼ NO                           │
│     ┌─────────────────┐           ┌─────────────────┐                      │
│     │                 │           │                 │                      │
│     │  Use SOFTIRQ    │           │  Use TASKLET    │                      │
│     │  🏎️             │           │  🚗             │                      │
│     │                 │           │                 │                      │
│     └─────────────────┘           └─────────────────┘                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 9: Timeline Visualization

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE TIMELINE VISUALIZATION                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TIME ───────────────────────────────────────────────────────────────▶    │
│                                                                            │
│        │                           HARDWARE INTERRUPT                      │
│        │                                  │                                │
│        │ User process                     ▼                                │
│        │ running          ┌───────────────────────────────┐                │
│        │ (Firefox)        │         TOP HALF              │                │
│        │    │             │    (Interrupt Handler)        │                │
│        │    │             │                               │                │
│        │    │             │ ⚡ Interrupts DISABLED        │                │
│        │    │             │                               │                │
│        │    │             │ 1. ACK hardware               │                │
│        │    │             │ 2. Save data to RAM           │                │
│        │    │             │ 3. Schedule bottom half       │                │
│        │    │             │                               │                │
│        │    │             │ Time: ~1-10 microseconds      │                │
│        │    │             └───────────────┬───────────────┘                │
│        │    │                             │                                │
│        │    │                             ▼                                │
│        │    │             ┌───────────────────────────────┐                │
│        │    │ return      │    Interrupts ENABLED again  │                │
│        │    │◄────────────│    Other interrupts can fire │                │
│        │    │             └───────────────────────────────┘                │
│        │    │                                                              │
│        │    ▼                                                              │
│        │ Firefox continues                                                 │
│        │ running...                                                        │
│        │    │                                                              │
│        │    │  At some point, kernel says:                                 │
│        │    │  "Time to run bottom halves"                                 │
│        │    │                                                              │
│        │    ▼                                                              │
│        │    ├─────────────────────────────────────────────┐                │
│        │                  │       BOTTOM HALF             │                │
│        │                  │   (Softirq/Tasklet)           │                │
│        │                  │                               │                │
│        │                  │ ✓ Interrupts ENABLED          │                │
│        │                  │                               │                │
│        │                  │ 1. Process the data           │                │
│        │                  │ 2. Parse headers              │                │
│        │                  │ 3. Route packet               │                │
│        │                  │ 4. Deliver to socket          │                │
│        │                  │ 5. Wake up Firefox            │                │
│        │                  │                               │                │
│        │                  │ Time: ~100+ microseconds      │                │
│        │                  └─────────────────────────────┬─┘                │
│        │                                                │                  │
│        │◄───────────────────────────────────────────────┘                  │
│        │                                                                   │
│        │ Firefox wakes up                                                  │
│        │ read() returns with data!                                         │
│        ▼                                                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### Part 10: Summary Table

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SUMMARY: DEFERRED WORK AT A GLANCE                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────┬─────────────────────────────────────────────────┐   │
│   │ Concept         │ One-Line Explanation                            │   │
│   ├─────────────────┼─────────────────────────────────────────────────┤   │
│   │ Interrupt       │ Hardware signal: "something happened, NOW!"     │   │
│   ├─────────────────┼─────────────────────────────────────────────────┤   │
│   │ Top Half        │ Quick handler - save critical data, exit fast   │   │
│   ├─────────────────┼─────────────────────────────────────────────────┤   │
│   │ Bottom Half     │ Deferred processing - handle the rest later     │   │
│   ├─────────────────┼─────────────────────────────────────────────────┤   │
│   │ Softirq         │ Fastest bottom half, for kernel experts only    │   │
│   ├─────────────────┼─────────────────────────────────────────────────┤   │
│   │ Tasklet         │ Easier bottom half, good for device drivers     │   │
│   ├─────────────────┼─────────────────────────────────────────────────┤   │
│   │ Workqueue       │ Flexible bottom half, can sleep and block       │   │
│   └─────────────────┴─────────────────────────────────────────────────┘   │
│                                                                            │
│   KEY INSIGHT:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   The entire purpose of top half / bottom half splitting is to      │ │
│   │   MINIMIZE the time spent with interrupts disabled, while still     │ │
│   │   ensuring no data is lost from hardware.                           │ │
│   │                                                                     │ │
│   │   Top half:  "Grab the data before it's lost!"                      │ │
│   │   Bottom half: "Now let's actually do something with it."           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Softirqs

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SOFTIRQS                                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Softirqs are statically allocated, high-priority deferred work           │
│   mechanisms. Only 10 softirqs exist in the kernel.                        │
│                                                                            │
│   SOFTIRQ TYPES:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌────────┬─────────────────────┬─────────────────────────────┐    │ │
│   │   │ Index  │ Name                │ Purpose                     │    │ │
│   │   ├────────┼─────────────────────┼─────────────────────────────┤    │ │
│   │   │ 0      │ HI_SOFTIRQ          │ High-priority tasklets      │    │ │
│   │   │ 1      │ TIMER_SOFTIRQ       │ Timer callbacks             │    │ │
│   │   │ 2      │ NET_TX_SOFTIRQ      │ Network transmit            │    │ │
│   │   │ 3      │ NET_RX_SOFTIRQ      │ Network receive             │    │ │
│   │   │ 4      │ BLOCK_SOFTIRQ       │ Block device completion     │    │ │
│   │   │ 5      │ IRQ_POLL_SOFTIRQ    │ IRQ polling                 │    │ │
│   │   │ 6      │ TASKLET_SOFTIRQ     │ Normal tasklets             │    │ │
│   │   │ 7      │ SCHED_SOFTIRQ       │ Scheduler load balancing    │    │ │
│   │   │ 8      │ HRTIMER_SOFTIRQ     │ High-resolution timers      │    │ │
│   │   │ 9      │ RCU_SOFTIRQ         │ RCU callbacks               │    │ │
│   │   └────────┴─────────────────────┴─────────────────────────────┘    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOFTIRQ EXECUTION:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Raising a softirq (from hardirq context) */                    │ │
│   │   raise_softirq(NET_RX_SOFTIRQ);                                    │ │
│   │                                                                     │ │
│   │   Softirqs run at these points:                                     │ │
│   │   1. After hardware interrupt handlers return                       │ │
│   │   2. In ksoftirqd kernel thread (when backlogged)                   │ │
│   │   3. Explicitly via local_bh_enable()                               │ │
│   │                                                                     │ │
│   │   /* do_softirq() execution flow */                                 │ │
│   │   do_softirq():                                                     │ │
│   │       while (pending = local_softirq_pending()) {                   │ │
│   │           local_irq_enable();    // Allow new hardirqs              │ │
│   │           for each pending softirq:                                 │ │
│   │               softirq_vec[i].action();                              │ │
│   │           local_irq_disable();                                      │ │
│   │           // If too many pending, wake ksoftirqd                    │ │
│   │       }                                                             │ │
│   │                                                                     │ │
│   │   IMPORTANT:                                                        │ │
│   │   • Same softirq can run on multiple CPUs simultaneously            │ │
│   │   • Handler must be fully reentrant and use per-CPU data            │ │
│   │   • Still cannot sleep (atomic context)                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Tasklets

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TASKLETS                                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Tasklets are built on top of softirqs but are dynamically allocatable    │
│   and simpler to use for driver writers.                                   │
│                                                                            │
│   TASKLET CHARACTERISTICS:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Dynamically created (unlike softirqs)                           │ │
│   │   • Same tasklet NEVER runs concurrently on multiple CPUs           │ │
│   │   • Different tasklets CAN run concurrently                         │ │
│   │   • Run in atomic context (cannot sleep)                            │ │
│   │   • Run on the CPU that scheduled them                              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TASKLET API:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Declare and initialize */                                      │ │
│   │   DECLARE_TASKLET(name, func);                                      │ │
│   │   /* or dynamically */                                              │ │
│   │   tasklet_init(&my_tasklet, my_tasklet_func, data);                 │ │
│   │                                                                     │ │
│   │   /* Schedule tasklet */                                            │ │
│   │   tasklet_schedule(&my_tasklet);      /* Normal priority */         │ │
│   │   tasklet_hi_schedule(&my_tasklet);   /* High priority */           │ │
│   │                                                                     │ │
│   │   /* Disable/enable */                                              │ │
│   │   tasklet_disable(&my_tasklet);       /* Wait and disable */        │ │
│   │   tasklet_enable(&my_tasklet);        /* Re-enable */               │ │
│   │   tasklet_kill(&my_tasklet);          /* Wait and remove */         │ │
│   │                                                                     │ │
│   │   /* Example */                                                     │ │
│   │   static void my_tasklet_handler(struct tasklet_struct *t)          │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = from_tasklet(dev, t, tasklet);        │ │
│   │       /* Process deferred work */                                   │ │
│   │       process_received_data(dev);                                   │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* In hardirq handler */                                          │ │
│   │   static irqreturn_t my_irq_handler(int irq, void *dev_id)          │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = dev_id;                               │ │
│   │       /* Quick: ack hardware, copy urgent data */                   │ │
│   │       dev->data = readl(dev->regs + DATA);                          │ │
│   │       /* Schedule tasklet for remaining work */                     │ │
│   │       tasklet_schedule(&dev->tasklet);                              │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Workqueues

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WORKQUEUES                                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Workqueues execute deferred work in process context, meaning they        │
│   CAN sleep. This is the most flexible deferred work mechanism.            │
│                                                                            │
│   WORKQUEUE CHARACTERISTICS:                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Run in kernel thread context (process context)                  │ │
│   │   • CAN sleep, block, and call sleeping functions                   │ │
│   │   • More overhead than softirqs/tasklets                            │ │
│   │   • Most common deferred work mechanism in drivers                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WORKQUEUE API:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Declare work structure */                                      │ │
│   │   DECLARE_WORK(name, func);                                         │ │
│   │   /* or dynamically */                                              │ │
│   │   INIT_WORK(&my_work, my_work_func);                                │ │
│   │                                                                     │ │
│   │   /* Schedule on system workqueue */                                │ │
│   │   schedule_work(&my_work);                                          │ │
│   │                                                                     │ │
│   │   /* Schedule with delay */                                         │ │
│   │   schedule_delayed_work(&my_delayed_work, msecs_to_jiffies(100));   │ │
│   │                                                                     │ │
│   │   /* Wait for completion */                                         │ │
│   │   flush_work(&my_work);           /* Wait for specific work */      │ │
│   │   flush_scheduled_work();         /* Wait for all work */           │ │
│   │   cancel_work_sync(&my_work);     /* Cancel and wait */             │ │
│   │                                                                     │ │
│   │   /* Example handler - CAN SLEEP! */                                │ │
│   │   static void my_work_handler(struct work_struct *work)             │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = container_of(work, struct my_device,  │ │
│   │                                            my_work);                │ │
│   │       void *buf = kmalloc(4096, GFP_KERNEL);  /* OK to sleep! */    │ │
│   │       mutex_lock(&dev->mutex);                /* OK to sleep! */    │ │
│   │       /* Do heavy processing */                                     │ │
│   │       process_data(dev, buf);                                       │ │
│   │       mutex_unlock(&dev->mutex);                                    │ │
│   │       kfree(buf);                                                   │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CUSTOM WORKQUEUES:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Create dedicated workqueue */                                  │ │
│   │   struct workqueue_struct *my_wq;                                   │ │
│   │   my_wq = create_workqueue("my_driver_wq");                         │ │
│   │   my_wq = create_singlethread_workqueue("my_driver_wq");            │ │
│   │   my_wq = alloc_workqueue("my_wq", WQ_UNBOUND | WQ_HIGHPRI, 0);     │ │
│   │                                                                     │ │
│   │   /* Schedule on custom workqueue */                                │ │
│   │   queue_work(my_wq, &my_work);                                      │ │
│   │   queue_delayed_work(my_wq, &my_delayed_work, delay);               │ │
│   │                                                                     │ │
│   │   /* Cleanup */                                                     │ │
│   │   destroy_workqueue(my_wq);                                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Threaded IRQs

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THREADED IRQS                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Threaded IRQs run the main interrupt handler in a dedicated kernel       │
│   thread, allowing it to sleep and use all kernel facilities.              │
│                                                                            │
│   API:                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int request_threaded_irq(                                         │ │
│   │       unsigned int irq,                                             │ │
│   │       irq_handler_t handler,        /* Hardirq handler (optional) */│ │
│   │       irq_handler_t thread_fn,      /* Thread handler */            │ │
│   │       unsigned long flags,                                          │ │
│   │       const char *name,                                             │ │
│   │       void *dev_id                                                  │ │
│   │   );                                                                │ │
│   │                                                                     │ │
│   │   Flow:                                                             │ │
│   │   1. Hardirq handler runs (optional) - returns IRQ_WAKE_THREAD      │ │
│   │   2. Kernel wakes dedicated irq/N-device thread                     │ │
│   │   3. Thread handler runs in process context                         │ │
│   │                                                                     │ │
│   │   /* Example */                                                     │ │
│   │   static irqreturn_t my_hardirq(int irq, void *dev_id)              │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = dev_id;                               │ │
│   │       if (!(readl(dev->regs + STATUS) & IRQ_PENDING))               │ │
│   │           return IRQ_NONE;                                          │ │
│   │       /* Disable device IRQ, will be re-enabled in thread */        │ │
│   │       writel(0, dev->regs + IRQ_ENABLE);                            │ │
│   │       return IRQ_WAKE_THREAD;                                       │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   static irqreturn_t my_thread_fn(int irq, void *dev_id)            │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = dev_id;                               │ │
│   │       /* Process context - can sleep! */                            │ │
│   │       mutex_lock(&dev->mutex);                                      │ │
│   │       do_heavy_work(dev);                                           │ │
│   │       mutex_unlock(&dev->mutex);                                    │ │
│   │       /* Re-enable device IRQ */                                    │ │
│   │       writel(1, dev->regs + IRQ_ENABLE);                            │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* Registration with IRQF_ONESHOT */                              │ │
│   │   request_threaded_irq(irq, my_hardirq, my_thread_fn,               │ │
│   │                        IRQF_ONESHOT, "my_device", dev);             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Deferred Work Comparison

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEFERRED WORK COMPARISON                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CHOOSING THE RIGHT MECHANISM:                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │              Can     Multi-CPU    Priority   Complexity             │ │
│   │              Sleep?  Concurrent?                                    │ │
│   │   ──────────────────────────────────────────────────────────        │ │
│   │   Softirq    No      Yes          Highest    Hard (fixed)           │ │
│   │   Tasklet    No      No (same)    High       Easy                   │ │
│   │   Workqueue  Yes     Yes          Normal     Easy                   │ │
│   │   Threaded   Yes     No (same)    Normal     Medium                 │ │
│   │   IRQ                                                               │ │
│   │                                                                     │ │
│   │   DECISION TREE:                                                    │ │
│   │                                                                     │ │
│   │   Need to sleep? ─────Yes────▶ Workqueue or Threaded IRQ            │ │
│   │        │                                                            │ │
│   │        No                                                           │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   Need highest     Yes                                              │ │
│   │   performance? ─────────────▶ Softirq (if allowed) or Tasklet       │ │
│   │        │                                                            │ │
│   │        No                                                           │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   Tasklet (simple, good default for atomic deferred work)           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Advanced Topics

### SMP and Interrupt Affinity

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SMP AND INTERRUPT AFFINITY                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   On SMP systems, interrupts can be directed to specific CPUs for          │
│   performance optimization and cache locality.                             │
│                                                                            │
│   INTERRUPT DISTRIBUTION:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Default: I/O APIC distributes interrupts (round-robin or lowest   │ │
│   │   priority CPU)                                                     │ │
│   │                                                                     │ │
│   │              Device IRQs                                            │ │
│   │                  │                                                  │ │
│   │                  ▼                                                  │ │
│   │           ┌──────────────┐                                          │ │
│   │           │   I/O APIC   │                                          │ │
│   │           └──────┬───────┘                                          │ │
│   │        ┌─────────┼─────────┐                                        │ │
│   │        ▼         ▼         ▼                                        │ │
│   │   ┌────────┐ ┌────────┐ ┌────────┐                                  │ │
│   │   │ CPU 0  │ │ CPU 1  │ │ CPU 2  │                                  │ │
│   │   └────────┘ └────────┘ └────────┘                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IRQ AFFINITY CONFIGURATION:                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* View current affinity */                                       │ │
│   │   $ cat /proc/irq/33/smp_affinity                                   │ │
│   │   0000000f    /* CPUs 0-3 (hex bitmask) */                          │ │
│   │                                                                     │ │
│   │   /* Set affinity to CPU 2 only */                                  │ │
│   │   $ echo 4 > /proc/irq/33/smp_affinity   /* 0100 binary = CPU 2 */  │ │
│   │                                                                     │ │
│   │   /* CPU list format */                                             │ │
│   │   $ cat /proc/irq/33/smp_affinity_list                              │ │
│   │   0-3                                                               │ │
│   │   $ echo 2 > /proc/irq/33/smp_affinity_list                         │ │
│   │                                                                     │ │
│   │   /* Kernel API */                                                  │ │
│   │   irq_set_affinity(irq, cpumask);                                   │ │
│   │   irq_set_affinity_hint(irq, cpumask);  /* Hint for balancer */     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IRQBALANCE DAEMON:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   The irqbalance daemon automatically distributes interrupts        │ │
│   │   across CPUs to optimize performance.                              │ │
│   │                                                                     │ │
│   │   Factors considered:                                               │ │
│   │   • CPU topology (NUMA nodes, cache sharing)                        │ │
│   │   • Interrupt frequency                                             │ │
│   │   • CPU load                                                        │ │
│   │   • Power management                                                │ │
│   │                                                                     │ │
│   │   $ systemctl status irqbalance                                     │ │
│   │   $ irqbalance --debug     /* See decisions */                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### NAPI (New API for Network Drivers)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NAPI (NEW API)                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   NAPI is a polling mechanism that reduces interrupt overhead under high   │
│   network load by switching between interrupt-driven and polling modes.    │
│                                                                            │
│   THE PROBLEM: INTERRUPT LIVELOCK                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   At high packet rates:                                             │ │
│   │   • Thousands of interrupts per second                              │ │
│   │   • Each interrupt has overhead (context switch, cache pollution)   │ │
│   │   • CPU spends all time handling interrupts                         │ │
│   │   • No time left to actually process packets!                       │ │
│   │   • System becomes unresponsive = "livelock"                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NAPI SOLUTION: HYBRID INTERRUPT/POLLING                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Low load:        ──────IRQ──────IRQ──────IRQ──────                │ │
│   │   (interrupt-driven, low latency)                                   │ │
│   │                                                                     │ │
│   │   High load:       ──IRQ──[disable]──poll──poll──poll──[enable]──   │ │
│   │   (polling mode, high throughput)                                   │ │
│   │                                                                     │ │
│   │   How it works:                                                     │ │
│   │   1. First packet arrives → interrupt                               │ │
│   │   2. Interrupt handler disables NIC interrupts                      │ │
│   │   3. Handler schedules NAPI poll                                    │ │
│   │   4. Softirq polls packets (no interrupts!)                         │ │
│   │   5. When RX queue empty, re-enable interrupts                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NAPI API:                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Initialize NAPI */                                             │ │
│   │   netif_napi_add(netdev, &dev->napi, my_poll, NAPI_POLL_WEIGHT);    │ │
│   │   napi_enable(&dev->napi);                                          │ │
│   │                                                                     │ │
│   │   /* In interrupt handler */                                        │ │
│   │   static irqreturn_t my_irq(int irq, void *dev_id)                  │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = dev_id;                               │ │
│   │       if (napi_schedule_prep(&dev->napi)) {                         │ │
│   │           disable_irq_nosync(dev->irq);  /* Disable NIC IRQ */      │ │
│   │           __napi_schedule(&dev->napi);                              │ │
│   │       }                                                             │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* NAPI poll function */                                          │ │
│   │   static int my_poll(struct napi_struct *napi, int budget)          │ │
│   │   {                                                                 │ │
│   │       int packets = 0;                                              │ │
│   │       while (packets < budget && hw_has_packet()) {                 │ │
│   │           process_packet();                                         │ │
│   │           packets++;                                                │ │
│   │       }                                                             │ │
│   │       if (packets < budget) {                                       │ │
│   │           /* Done - re-enable interrupts */                         │ │
│   │           napi_complete_done(napi, packets);                        │ │
│   │           enable_irq(dev->irq);                                     │ │
│   │       }                                                             │ │
│   │       return packets;                                               │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Interrupt Coalescing

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERRUPT COALESCING                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Hardware-level technique to reduce interrupt rate by batching events.    │
│                                                                            │
│   WITHOUT COALESCING:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Packets:    P1────P2────P3────P4────P5────P6────                  │ │
│   │   IRQs:       ↑     ↑     ↑     ↑     ↑     ↑                       │ │
│   │               (6 interrupts for 6 packets)                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WITH COALESCING (count=3):                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Packets:    P1────P2────P3────P4────P5────P6────                  │ │
│   │   IRQs:                   ↑                 ↑                       │ │
│   │               (2 interrupts for 6 packets)                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COALESCING PARAMETERS:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • rx-usecs: Max microseconds to wait before interrupt             │ │
│   │   • rx-frames: Max packets to queue before interrupt                │ │
│   │   • tx-usecs/tx-frames: Same for transmit                           │ │
│   │   • adaptive: Hardware adjusts based on load                        │ │
│   │                                                                     │ │
│   │   /* Configure with ethtool */                                      │ │
│   │   $ ethtool -c eth0                /* Show current settings */      │ │
│   │   $ ethtool -C eth0 rx-usecs 100 rx-frames 64                       │ │
│   │   $ ethtool -C eth0 adaptive-rx on                                  │ │
│   │                                                                     │ │
│   │   TRADEOFF:                                                         │ │
│   │   • More coalescing = Higher throughput, lower CPU usage            │ │
│   │   • Less coalescing = Lower latency, higher CPU usage               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Considerations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME CONSIDERATIONS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Real-time systems require deterministic interrupt latency - the time     │
│   from interrupt assertion to handler execution must be bounded.           │
│                                                                            │
│   LATENCY COMPONENTS:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   IRQ ──▶ Handler                                                   │ │
│   │   │       │                                                         │ │
│   │   │   ┌───┴───────────────────────────────────────────────┐         │ │
│   │   │   │ • Hardware detection time                         │         │ │
│   │   │   │ • Interrupt controller routing                    │         │ │
│   │   │   │ • Current instruction completion                  │         │ │
│   │   │   │ • IDT lookup and privilege switch                 │         │ │
│   │   │   │ • Register save                                   │         │ │
│   │   │   │ • Kernel entry code                               │         │ │
│   │   │   └───────────────────────────────────────────────────┘         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PREEMPT_RT PATCH (Real-Time Linux):                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Key changes for determinism:                                      │ │
│   │                                                                     │ │
│   │   1. THREADED INTERRUPTS BY DEFAULT                                 │ │
│   │      Most handlers run in kernel threads (can be preempted)         │ │
│   │                                                                     │ │
│   │   2. SLEEPING SPINLOCKS                                             │ │
│   │      Spinlocks become rt_mutex (can sleep, inherit priority)        │ │
│   │                                                                     │ │
│   │   3. HIGH-RESOLUTION TIMERS                                         │ │
│   │      Microsecond-precision timer events                             │ │
│   │                                                                     │ │
│   │   4. PRIORITY INHERITANCE                                           │ │
│   │      Prevents priority inversion                                    │ │
│   │                                                                     │ │
│   │   /* Enable RT scheduling for IRQ thread */                         │ │
│   │   $ chrt -f -p 90 $(pgrep irq/33-eth0)                              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MEASURING LATENCY:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* cyclictest - standard RT latency measurement */                │ │
│   │   $ cyclictest -p 90 -m -i 1000 -l 10000                            │ │
│   │   # T: 0 Min:      1 Act:    5 Avg:    3 Max:      42               │ │
│   │                                                                     │ │
│   │   /* ftrace interrupt latency tracer */                             │ │
│   │   $ echo irqsoff > /sys/kernel/debug/tracing/current_tracer         │ │
│   │   $ cat /sys/kernel/debug/tracing/tracing_max_latency               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 11. Practical Implementation

### Writing Interrupt Handlers

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WRITING INTERRUPT HANDLERS                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A well-designed interrupt handler follows these principles:              │
│                                                                            │
│   HANDLER TEMPLATE:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   static irqreturn_t my_handler(int irq, void *dev_id)              │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = dev_id;                               │ │
│   │       u32 status;                                                   │ │
│   │                                                                     │ │
│   │       /* 1. CHECK: Is this interrupt for us? */                     │ │
│   │       status = readl(dev->regs + IRQ_STATUS);                       │ │
│   │       if (!(status & OUR_IRQ_BITS))                                 │ │
│   │           return IRQ_NONE;   /* Not our interrupt */                │ │
│   │                                                                     │ │
│   │       /* 2. ACK: Acknowledge the interrupt to hardware */           │ │
│   │       writel(status, dev->regs + IRQ_ACK);                          │ │
│   │                                                                     │ │
│   │       /* 3. HANDLE: Do minimal work - defer the rest */             │ │
│   │       dev->irq_status = status;                                     │ │
│   │       if (status & RX_READY)                                        │ │
│   │           tasklet_schedule(&dev->rx_tasklet);                       │ │
│   │       if (status & TX_COMPLETE)                                     │ │
│   │           wake_up(&dev->tx_wait);                                   │ │
│   │                                                                     │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY PRINCIPLES:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. VERIFY OWNERSHIP                                               │ │
│   │      Always check if interrupt is yours (shared IRQ lines)          │ │
│   │                                                                     │ │
│   │   2. ACKNOWLEDGE QUICKLY                                            │ │
│   │      Clear interrupt source to prevent re-triggering                │ │
│   │                                                                     │ │
│   │   3. MINIMIZE TIME IN HANDLER                                       │ │
│   │      Do only what MUST be done with interrupts disabled             │ │
│   │                                                                     │ │
│   │   4. DEFER HEAVY WORK                                               │ │
│   │      Use tasklets/workqueues for processing                         │ │
│   │                                                                     │ │
│   │   5. NO SLEEPING                                                    │ │
│   │      Never call functions that might sleep                          │ │
│   │                                                                     │ │
│   │   6. USE SPINLOCKS CAREFULLY                                        │ │
│   │      Use spin_lock() not spin_lock_irqsave() (already disabled)     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Complete Driver Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE DRIVER EXAMPLE                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   /* Simplified character device driver with interrupt handling */         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   #include <linux/module.h>                                         │ │
│   │   #include <linux/interrupt.h>                                      │ │
│   │   #include <linux/platform_device.h>                                │ │
│   │                                                                     │ │
│   │   struct my_device {                                                │ │
│   │       void __iomem *regs;                                           │ │
│   │       int irq;                                                      │ │
│   │       spinlock_t lock;                                              │ │
│   │       struct tasklet_struct tasklet;                                │ │
│   │       wait_queue_head_t wait;                                       │ │
│   │       u32 data_ready;                                               │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   /* Tasklet - deferred work in softirq context */                  │ │
│   │   static void my_tasklet_handler(struct tasklet_struct *t)          │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = from_tasklet(dev, t, tasklet);        │ │
│   │       /* Process received data - can take longer */                 │ │
│   │       process_received_data(dev);                                   │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* Interrupt handler - minimal work */                            │ │
│   │   static irqreturn_t my_irq_handler(int irq, void *dev_id)          │ │
│   │   {                                                                 │ │
│   │       struct my_device *dev = dev_id;                               │ │
│   │       u32 status = readl(dev->regs + STATUS_REG);                   │ │
│   │                                                                     │ │
│   │       if (!(status & IRQ_PENDING))                                  │ │
│   │           return IRQ_NONE;                                          │ │
│   │                                                                     │ │
│   │       /* Acknowledge interrupt */                                   │ │
│   │       writel(IRQ_ACK, dev->regs + IRQ_REG);                         │ │
│   │                                                                     │ │
│   │       /* Schedule deferred work */                                  │ │
│   │       spin_lock(&dev->lock);                                        │ │
│   │       dev->data_ready = 1;                                          │ │
│   │       spin_unlock(&dev->lock);                                      │ │
│   │                                                                     │ │
│   │       tasklet_schedule(&dev->tasklet);                              │ │
│   │       wake_up_interruptible(&dev->wait);                            │ │
│   │                                                                     │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Debugging Interrupts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEBUGGING INTERRUPTS                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   /proc/interrupts - INTERRUPT STATISTICS:                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   $ cat /proc/interrupts                                            │ │
│   │              CPU0       CPU1       CPU2       CPU3                  │ │
│   │     0:         45          0          0          0   IO-APIC   2-   │ │
│   │     1:          2          0          0          0   IO-APIC   1-   │ │
│   │     8:          0          0          0          0   IO-APIC   8-   │ │
│   │    12:        138          0          0          0   IO-APIC  12-   │ │
│   │    16:      28433       8721      10234       9887   IO-APIC  16-   │ │
│   │    33:    1234567     234567     345678     456789   PCI-MSI  524288│ │
│   │   NMI:        123        124        125        126   Non-maskable   │ │
│   │   LOC:    9876543    8765432    7654321    6543210   Local timer    │ │
│   │   RES:      12345      11234      10123       9012   Rescheduling   │ │
│   │   CAL:       1234       1123       1012        901   Function call  │ │
│   │                                                                     │ │
│   │   Column meanings:                                                  │ │
│   │   • Per-CPU interrupt counts                                        │ │
│   │   • IRQ type (IO-APIC, PCI-MSI, etc.)                              │ │
│   │   • IRQ number/identifier                                           │ │
│   │   • Device name(s) sharing this IRQ                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   /proc/irq/N/* - PER-IRQ DETAILS:                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   $ ls /proc/irq/33/                                                │ │
│   │   affinity_hint  effective_affinity  node                           │ │
│   │   chip_name      effective_affinity_list  smp_affinity              │ │
│   │   hwirq          spurious            smp_affinity_list              │ │
│   │                                                                     │ │
│   │   $ cat /proc/irq/33/spurious                                       │ │
│   │   count 0                                                           │ │
│   │   unhandled 0                                                       │ │
│   │   last_unhandled 0 ms                                               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   FTRACE FOR INTERRUPT TRACING:                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Trace all interrupt handlers */                                │ │
│   │   $ cd /sys/kernel/debug/tracing                                    │ │
│   │   $ echo function > current_tracer                                  │ │
│   │   $ echo '*_irq*' > set_ftrace_filter                               │ │
│   │   $ echo 1 > tracing_on                                             │ │
│   │   $ cat trace                                                       │ │
│   │                                                                     │ │
│   │   /* Trace IRQ disable/enable times */                              │ │
│   │   $ echo irqsoff > current_tracer                                   │ │
│   │   $ echo 1 > tracing_on                                             │ │
│   │   /* ... run workload ... */                                        │ │
│   │   $ cat tracing_max_latency                                         │ │
│   │   $ cat trace     /* Shows longest IRQ-disabled section */          │ │
│   │                                                                     │ │
│   │   /* Hardware latency detector */                                   │ │
│   │   $ echo hwlat > current_tracer                                     │ │
│   │   $ cat trace     /* Shows SMI and other hardware latencies */      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DEBUGGING COMMON ISSUES:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Issue: "Nobody cared" messages in dmesg                           │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │ irq 33: nobody cared (try booting with "irqpoll" option)    │   │ │
│   │   │ handlers:                                                   │   │ │
│   │   │ [<ffffffff8123abcd>] my_irq_handler                         │   │ │
│   │   │ Disabling IRQ #33                                           │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   Cause: Handler returns IRQ_HANDLED for spurious interrupts        │ │
│   │   Fix: Properly check hardware status before returning IRQ_HANDLED  │ │
│   │                                                                     │ │
│   │   Issue: Interrupt storms (high CPU usage)                          │ │
│   │   • Check /proc/interrupts for rapidly increasing counts            │ │
│   │   • May indicate stuck interrupt (edge/level mismatch)              │ │
│   │   • May indicate missing ACK to hardware                            │ │
│   │                                                                     │ │
│   │   Issue: Lost interrupts                                            │ │
│   │   • Check affinity - may be going to wrong CPU                      │ │
│   │   • Verify interrupt is enabled in hardware and kernel              │ │
│   │   • Check for IRQ conflicts                                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Common Mistakes to Avoid

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMMON MISTAKES TO AVOID                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✗ MISTAKE 1: SLEEPING IN INTERRUPT CONTEXT                        │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │   /* WRONG - will cause kernel panic! */                    │   │ │
│   │   │   static irqreturn_t bad_handler(int irq, void *dev_id)     │   │ │
│   │   │   {                                                         │   │ │
│   │   │       mutex_lock(&my_mutex);      /* Can sleep! */          │   │ │
│   │   │       kmalloc(size, GFP_KERNEL);  /* Can sleep! */          │   │ │
│   │   │       copy_from_user(...);        /* Can sleep! */          │   │ │
│   │   │   }                                                         │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │   Fix: Use spin_lock(), GFP_ATOMIC, defer work to process context  │ │
│   │                                                                     │ │
│   │   ✗ MISTAKE 2: HOLDING SPINLOCK TOO LONG                            │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │   /* WRONG - other CPUs spin waiting */                     │   │ │
│   │   │   spin_lock(&lock);                                         │   │ │
│   │   │   for (i = 0; i < 10000; i++)                               │   │ │
│   │   │       process_item(i);    /* Long operation */              │   │ │
│   │   │   spin_unlock(&lock);                                       │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │   Fix: Minimize critical section, defer to tasklet/workqueue       │ │
│   │                                                                     │ │
│   │   ✗ MISTAKE 3: FORGETTING TO ACK INTERRUPT                          │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │   /* WRONG - interrupt keeps firing! */                     │   │ │
│   │   │   static irqreturn_t bad_handler(int irq, void *dev_id)     │   │ │
│   │   │   {                                                         │   │ │
│   │   │       process_interrupt();                                  │   │ │
│   │   │       /* Forgot to ACK hardware! */                         │   │ │
│   │   │       return IRQ_HANDLED;                                   │   │ │
│   │   │   }                                                         │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │   Fix: Always write to hardware ACK register                       │ │
│   │                                                                     │ │
│   │   ✗ MISTAKE 4: RETURNING IRQ_HANDLED FOR WRONG INTERRUPT            │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │   /* WRONG - masks other device's interrupt! */             │   │ │
│   │   │   static irqreturn_t bad_handler(int irq, void *dev_id)     │   │ │
│   │   │   {                                                         │   │ │
│   │   │       /* No check if interrupt is ours */                   │   │ │
│   │   │       return IRQ_HANDLED;  /* Always! */                    │   │ │
│   │   │   }                                                         │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │   Fix: Check hardware status, return IRQ_NONE if not yours         │ │
│   │                                                                     │ │
│   │   ✗ MISTAKE 5: RACE BETWEEN HANDLER AND DRIVER CODE                 │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │   /* WRONG - data race between handler and process ctx */   │   │ │
│   │   │   /* In handler: */                                         │   │ │
│   │   │   dev->buffer[dev->write_pos++] = data;                     │   │ │
│   │   │                                                             │   │ │
│   │   │   /* In process context: */                                 │   │ │
│   │   │   data = dev->buffer[dev->read_pos++];                      │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │   Fix: Use spin_lock_irqsave() in process context, spin_lock() in │ │
│   │        handler, or use lock-free ring buffers                      │ │
│   │                                                                     │ │
│   │   ✗ MISTAKE 6: INCORRECT IRQF_SHARED USAGE                          │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │   /* WRONG - can't share without IRQF_SHARED */             │   │ │
│   │   │   request_irq(irq, handler, 0, "my_dev", NULL);             │   │ │
│   │   │                /* ↑ No IRQF_SHARED */  /* ↑ NULL dev_id! */ │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │   Fix: Use IRQF_SHARED and unique non-NULL dev_id                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Understanding Mutex vs Spinlock

The following section explains why we use `spin_lock()` instead of `mutex_lock()` in
interrupt context, and the fundamental differences between these two locking mechanisms.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MUTEX vs SPINLOCK - THE KEY DIFFERENCE                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHAT HAPPENS WHEN THE LOCK IS ALREADY TAKEN?                             │
│                                                                            │
│   MUTEX (mutex_lock):                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Thread A holds lock                                               │ │
│   │        │                                                            │ │
│   │   Thread B wants lock                                               │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   ┌─────────────────────────────────────────────────────────┐       │ │
│   │   │  "Lock is taken? OK, I'll go to SLEEP 😴"               │       │ │
│   │   │                                                         │       │ │
│   │   │  Thread B is PUT TO SLEEP (removed from CPU)            │       │ │
│   │   │  CPU can run OTHER processes while waiting              │       │ │
│   │   │  When lock is free, Thread B is WOKEN UP                │       │ │
│   │   └─────────────────────────────────────────────────────────┘       │ │
│   │                                                                     │ │
│   │   ✓ Efficient for LONG waits (CPU does useful work)                 │ │
│   │   ✗ CANNOT be used in interrupt context (no process to sleep!)     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SPINLOCK (spin_lock):                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Thread A holds lock                                               │ │
│   │        │                                                            │ │
│   │   Thread B wants lock                                               │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   ┌─────────────────────────────────────────────────────────┐       │ │
│   │   │  "Lock is taken? I'll keep CHECKING! 🔄"                │       │ │
│   │   │                                                         │       │ │
│   │   │  while (lock is taken) {                                │       │ │
│   │   │      // do nothing, just spin!                          │       │ │
│   │   │      // CPU is BUSY doing nothing useful                │       │ │
│   │   │  }                                                      │       │ │
│   │   └─────────────────────────────────────────────────────────┘       │ │
│   │                                                                     │ │
│   │   ✓ CAN be used in interrupt context (doesn't need to sleep)       │ │
│   │   ✗ Wastes CPU cycles while waiting (busy-waiting)                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WHY MUTEX CAN'T BE USED IN INTERRUPTS                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   To understand this, you need to know HOW sleeping works:                 │
│                                                                            │
│   NORMAL PROCESS CONTEXT:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Process A running                                                 │ │
│   │        │                                                            │ │
│   │        ▼ calls mutex_lock() (lock is taken)                         │ │
│   │        │                                                            │ │
│   │   ┌────┴────────────────────────────────────────┐                   │ │
│   │   │ Scheduler says:                             │                   │ │
│   │   │ "Process A wants to sleep"                  │                   │ │
│   │   │                                             │                   │ │
│   │   │ 1. Save Process A's state                   │                   │ │
│   │   │ 2. Mark A as "sleeping"                     │                   │ │
│   │   │ 3. Pick another process to run              │                   │ │
│   │   │ 4. Switch to that process                   │                   │ │
│   │   └─────────────────────────────────────────────┘                   │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   Process B runs (CPU doing useful work!)                           │ │
│   │                                                                     │ │
│   │   Later, when lock is released:                                     │ │
│   │   Scheduler wakes up Process A, it continues                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   INTERRUPT CONTEXT:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Process A was running                                             │ │
│   │        │                                                            │ │
│   │        ▼ INTERRUPT! (hardware interrupt fires)                      │ │
│   │        │                                                            │ │
│   │   ┌────┴────────────────────────────────────────┐                   │ │
│   │   │ CPU jumps to interrupt handler              │                   │ │
│   │   │                                             │                   │ │
│   │   │ • There is NO "current process" to sleep    │                   │ │
│   │   │ • We interrupted Process A, we didn't       │                   │ │
│   │   │   "become" Process A                        │                   │ │
│   │   │ • We're in a special "interrupt context"    │                   │ │
│   │   │ • Scheduler CANNOT run here                 │                   │ │
│   │   │ • We MUST return quickly to let A continue  │                   │ │
│   │   └─────────────────────────────────────────────┘                   │ │
│   │        │                                                            │ │
│   │        ▼ If we try to sleep here...                                 │ │
│   │        │                                                            │ │
│   │   ┌────┴────────────────────────────────────────┐                   │ │
│   │   │ 💥 KERNEL PANIC! 💥                         │                   │ │
│   │   │                                             │                   │ │
│   │   │ "BUG: scheduling while atomic"              │                   │ │
│   │   │                                             │                   │ │
│   │   │ The kernel detects you tried to sleep       │                   │ │
│   │   │ in a context where sleeping is forbidden    │                   │ │
│   │   └─────────────────────────────────────────────┘                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMPARISON TABLE: MUTEX vs SPINLOCK                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌────────────────────┬────────────────────┬────────────────────────────┐ │
│   │ Feature            │ MUTEX              │ SPINLOCK                   │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ Waiting behavior   │ Sleep (yield CPU)  │ Spin (busy-wait)           │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ CPU usage while    │ 0% (sleeping)      │ 100% (spinning)            │ │
│   │ waiting            │                    │                            │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ Use in interrupt?  │ ❌ NO (will panic) │ ✅ YES                     │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ Use in softirq?    │ ❌ NO              │ ✅ YES                     │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ Use in tasklet?    │ ❌ NO              │ ✅ YES                     │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ Use in workqueue?  │ ✅ YES             │ ✅ YES                     │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ Use in process     │ ✅ YES             │ ✅ YES (but wasteful)      │ │
│   │ context?           │                    │                            │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ Hold duration      │ Can be long        │ MUST be very short         │ │
│   ├────────────────────┼────────────────────┼────────────────────────────┤ │
│   │ Overhead           │ Higher (sleep/wake)│ Lower (just spin)          │ │
│   └────────────────────┴────────────────────┴────────────────────────────┘ │
│                                                                            │
│   RULE OF THUMB:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • In INTERRUPT context → Use SPINLOCK (no choice!)                │ │
│   │                                                                     │ │
│   │   • In PROCESS context, lock held SHORT time → Spinlock is fine     │ │
│   │                                                                     │ │
│   │   • In PROCESS context, lock held LONG time → Use MUTEX             │ │
│   │     (so other processes can use the CPU while you wait)             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ANALOGY: WAITING FOR A BATHROOM                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   MUTEX (Sleeping Lock):                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   🚻 Bathroom occupied                                              │ │
│   │                                                                     │ │
│   │   You: "I'll go sit on the couch and watch TV 📺"                   │ │
│   │        "Someone will tell me when it's free"                        │ │
│   │                                                                     │ │
│   │   → You're doing something useful while waiting                     │ │
│   │   → But you need a couch (process context) to sit on!               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SPINLOCK (Busy-Wait Lock):                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   🚻 Bathroom occupied                                              │ │
│   │                                                                     │ │
│   │   You: *stands at door, jiggling handle repeatedly* 🔄              │ │
│   │        "Is it free? No. Is it free? No. Is it free? No..."         │ │
│   │                                                                     │ │
│   │   → You're wasting energy doing nothing useful                      │ │
│   │   → But you don't need anywhere to sit!                             │ │
│   │   → Works even if there's no couch (interrupt context)              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT SUMMARY: WHERE CAN YOU USE WHAT?                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌───────────────────┬───────────┬────────────┬─────────────────────────┐ │
│   │ Context           │ Can Sleep?│ Use Mutex? │ Use Spinlock?           │ │
│   ├───────────────────┼───────────┼────────────┼─────────────────────────┤ │
│   │ Interrupt handler │ ❌ NO     │ ❌ NO      │ ✅ YES                  │ │
│   ├───────────────────┼───────────┼────────────┼─────────────────────────┤ │
│   │ Softirq           │ ❌ NO     │ ❌ NO      │ ✅ YES                  │ │
│   ├───────────────────┼───────────┼────────────┼─────────────────────────┤ │
│   │ Tasklet           │ ❌ NO     │ ❌ NO      │ ✅ YES                  │ │
│   ├───────────────────┼───────────┼────────────┼─────────────────────────┤ │
│   │ Workqueue         │ ✅ YES    │ ✅ YES     │ ✅ YES                  │ │
│   ├───────────────────┼───────────┼────────────┼─────────────────────────┤ │
│   │ Kernel thread     │ ✅ YES    │ ✅ YES     │ ✅ YES                  │ │
│   ├───────────────────┼───────────┼────────────┼─────────────────────────┤ │
│   │ System call       │ ✅ YES    │ ✅ YES     │ ✅ YES                  │ │
│   │ (process context) │           │            │                         │ │
│   └───────────────────┴───────────┴────────────┴─────────────────────────┘ │
│                                                                            │
│   KEY INSIGHT:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   In interrupt context, there's NO process to put to sleep,         │ │
│   │   so you MUST use spinlock.                                         │ │
│   │                                                                     │ │
│   │   In process context, you have a choice:                            │ │
│   │   • Use MUTEX for longer waits (more efficient - CPU can do         │ │
│   │     other work while you wait)                                      │ │
│   │   • Use SPINLOCK for very short waits (lower overhead)              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SPINLOCK VARIANTS FOR DIFFERENT SITUATIONS              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Different spinlock functions for different situations:                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   spin_lock(&lock)                                                  │ │
│   │   └── Use when: Already in interrupt context, or interrupts         │ │
│   │       don't touch the data protected by this lock                   │ │
│   │                                                                     │ │
│   │   spin_lock_irq(&lock)                                              │ │
│   │   └── Disables interrupts, then takes lock                          │ │
│   │       Use when: In process context, interrupt handlers also use     │ │
│   │       this lock, and you know interrupts are currently enabled      │ │
│   │                                                                     │ │
│   │   spin_lock_irqsave(&lock, flags)                                   │ │
│   │   └── Saves interrupt state, disables interrupts, takes lock        │ │
│   │       Use when: In process context, interrupt handlers also use     │ │
│   │       this lock, and you don't know current interrupt state         │ │
│   │       (SAFEST option for shared data)                               │ │
│   │                                                                     │ │
│   │   spin_lock_bh(&lock)                                               │ │
│   │   └── Disables softirqs/tasklets, then takes lock                   │ │
│   │       Use when: Softirqs/tasklets also use this lock                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY DO WE NEED THESE VARIANTS?                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Problem: DEADLOCK if you hold a spinlock and get interrupted      │ │
│   │   by code that tries to take the same lock!                         │ │
│   │                                                                     │ │
│   │   Process context:                                                  │ │
│   │        │                                                            │ │
│   │        ▼ spin_lock(&lock)  ← Takes lock                             │ │
│   │        │                                                            │ │
│   │        ▼ INTERRUPT! ← Handler runs                                  │ │
│   │        │                                                            │ │
│   │        ▼ Handler: spin_lock(&lock) ← Tries to take same lock        │ │
│   │        │                                                            │ │
│   │   💥 DEADLOCK! Handler waits forever for lock that                  │ │
│   │      process context holds, but process context can't               │ │
│   │      continue until handler finishes!                               │ │
│   │                                                                     │ │
│   │   Solution: Use spin_lock_irqsave() to disable interrupts           │ │
│   │   before taking the lock in process context                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE: CORRECT USAGE                                                   │ │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* In interrupt handler - interrupts already disabled */          │ │
│   │   static irqreturn_t my_handler(int irq, void *dev_id)              │ │
│   │   {                                                                 │ │
│   │       spin_lock(&dev->lock);    /* Simple spin_lock is fine */      │ │
│   │       dev->data_ready = 1;                                          │ │
│   │       spin_unlock(&dev->lock);                                      │ │
│   │       return IRQ_HANDLED;                                           │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* In process context (e.g., read system call) */                 │ │
│   │   static ssize_t my_read(struct file *file, char __user *buf, ...)  │ │
│   │   {                                                                 │ │
│   │       unsigned long flags;                                          │ │
│   │                                                                     │ │
│   │       spin_lock_irqsave(&dev->lock, flags);  /* Disable interrupts */│ │
│   │       data = dev->data_ready;                                       │ │
│   │       spin_unlock_irqrestore(&dev->lock, flags);  /* Restore */     │ │
│   │                                                                     │ │
│   │       /* Now interrupts can fire again safely */                    │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 12. Summary and Reference

### Quick Reference: API Summary

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERRUPT API QUICK REFERENCE                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   IRQ REGISTRATION:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Basic registration */                                          │ │
│   │   int request_irq(irq, handler, flags, name, dev_id);               │ │
│   │                                                                     │ │
│   │   /* Threaded IRQ */                                                │ │
│   │   int request_threaded_irq(irq, handler, thread_fn, flags,          │ │
│   │                            name, dev_id);                           │ │
│   │                                                                     │ │
│   │   /* Managed (devm) - auto cleanup on device removal */             │ │
│   │   int devm_request_irq(dev, irq, handler, flags, name, dev_id);     │ │
│   │                                                                     │ │
│   │   /* Unregistration */                                              │ │
│   │   void free_irq(irq, dev_id);                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IRQ FLAGS:                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   IRQF_SHARED           Share IRQ line with other devices           │ │
│   │   IRQF_TRIGGER_RISING   Rising edge triggered                       │ │
│   │   IRQF_TRIGGER_FALLING  Falling edge triggered                      │ │
│   │   IRQF_TRIGGER_HIGH     Level triggered, active high                │ │
│   │   IRQF_TRIGGER_LOW      Level triggered, active low                 │ │
│   │   IRQF_ONESHOT          Keep disabled until thread completes        │ │
│   │   IRQF_NO_THREAD        Never thread this handler (RT)              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   RETURN VALUES:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   IRQ_NONE           Interrupt not from this device                 │ │
│   │   IRQ_HANDLED        Interrupt successfully handled                 │ │
│   │   IRQ_WAKE_THREAD    Wake handler thread (threaded IRQ)             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IRQ CONTROL:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   local_irq_disable()         Disable IRQs on local CPU             │ │
│   │   local_irq_enable()          Enable IRQs on local CPU              │ │
│   │   local_irq_save(flags)       Save state and disable                │ │
│   │   local_irq_restore(flags)    Restore saved state                   │ │
│   │                                                                     │ │
│   │   disable_irq(irq)            Disable specific IRQ (waits)          │ │
│   │   disable_irq_nosync(irq)     Disable without waiting               │ │
│   │   enable_irq(irq)             Enable specific IRQ                   │ │
│   │   irq_set_affinity(irq, mask) Set CPU affinity                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Quick Reference: Deferred Work

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEFERRED WORK QUICK REFERENCE                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TASKLETS (softirq context, cannot sleep):                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   DECLARE_TASKLET(name, func);            /* Static */              │ │
│   │   tasklet_setup(&tasklet, func);          /* Dynamic */             │ │
│   │   tasklet_schedule(&tasklet);             /* Schedule */            │ │
│   │   tasklet_hi_schedule(&tasklet);          /* High priority */       │ │
│   │   tasklet_disable(&tasklet);              /* Disable */             │ │
│   │   tasklet_kill(&tasklet);                 /* Remove */              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WORKQUEUES (process context, CAN sleep):                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   INIT_WORK(&work, func);                 /* Initialize */          │ │
│   │   schedule_work(&work);                   /* System WQ */           │ │
│   │   schedule_delayed_work(&dwork, delay);   /* Delayed */             │ │
│   │   queue_work(wq, &work);                  /* Custom WQ */           │ │
│   │   flush_work(&work);                      /* Wait complete */       │ │
│   │   cancel_work_sync(&work);                /* Cancel + wait */       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Key Concepts Summary

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KEY CONCEPTS SUMMARY                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   INTERRUPT FUNDAMENTALS:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Interrupts are ASYNCHRONOUS signals to the CPU                  │ │
│   │   • They preempt current execution for urgent events                │ │
│   │   • Hardware interrupts come from devices (async, external)         │ │
│   │   • Software interrupts/exceptions from CPU (sync, internal)        │ │
│   │   • Each interrupt has a VECTOR number (index into IDT)             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   INTERRUPT HANDLING FLOW:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Device ──▶ IRQ Controller ──▶ CPU ──▶ IDT ──▶ Handler             │ │
│   │                                                                     │ │
│   │   1. Device asserts IRQ line                                        │ │
│   │   2. Interrupt controller (APIC) routes to CPU                      │ │
│   │   3. CPU saves state, looks up handler in IDT                       │ │
│   │   4. Handler executes (top half)                                    │ │
│   │   5. Deferred work runs later (bottom half)                         │ │
│   │   6. IRET restores state, resumes execution                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TOP HALF vs BOTTOM HALF:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   TOP HALF (Hardirq Handler):                                       │ │
│   │   • Runs with interrupts disabled                                   │ │
│   │   • Must be FAST - minimal work only                                │ │
│   │   • Cannot sleep, cannot access user memory                         │ │
│   │   • Acknowledge interrupt, schedule deferred work                   │ │
│   │                                                                     │ │
│   │   BOTTOM HALF (Deferred Work):                                      │ │
│   │   • Softirqs/Tasklets: Still atomic, cannot sleep                   │ │
│   │   • Workqueues: Process context, CAN sleep                          │ │
│   │   • Do the heavy lifting here                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONTEXT RULES:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │                        │ Process │ Softirq │ Hardirq                │ │
│   │   ─────────────────────┼─────────┼─────────┼─────────               │ │
│   │   Can sleep?           │   Yes   │   No    │   No                   │ │
│   │   Can access user mem? │   Yes   │   No    │   No                   │ │
│   │   Has process context? │   Yes   │   No    │   No                   │ │
│   │   Can be preempted?    │   Yes   │ By IRQ  │   No                   │ │
│   │   Use mutex?           │   Yes   │   No    │   No                   │ │
│   │   Use spinlock?        │   Yes*  │   Yes   │   Yes                  │ │
│   │                        │ *irqsave│         │                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### x86 Exception Vector Table

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    x86 EXCEPTION VECTORS (0-31)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Vec │ Name                    │ Type   │ Error Code │ Description        │
│   ────┼─────────────────────────┼────────┼────────────┼──────────────────  │
│    0  │ #DE Divide Error        │ Fault  │ No         │ DIV/IDIV by 0      │
│    1  │ #DB Debug               │ F/T    │ No         │ Debug exception    │
│    2  │ NMI                     │ Int    │ No         │ Non-maskable       │
│    3  │ #BP Breakpoint          │ Trap   │ No         │ INT3 instruction   │
│    4  │ #OF Overflow            │ Trap   │ No         │ INTO instruction   │
│    5  │ #BR Bound Range         │ Fault  │ No         │ BOUND exceeded     │
│    6  │ #UD Invalid Opcode      │ Fault  │ No         │ Undefined opcode   │
│    7  │ #NM No Math             │ Fault  │ No         │ FPU not available  │
│    8  │ #DF Double Fault        │ Abort  │ Yes (0)    │ Double exception   │
│   10  │ #TS Invalid TSS         │ Fault  │ Yes        │ Bad TSS            │
│   11  │ #NP Segment Not Present │ Fault  │ Yes        │ Segment missing    │
│   12  │ #SS Stack Segment       │ Fault  │ Yes        │ Stack fault        │
│   13  │ #GP General Protection  │ Fault  │ Yes        │ Protection viol.   │
│   14  │ #PF Page Fault          │ Fault  │ Yes        │ Page not present   │
│   16  │ #MF Math Fault          │ Fault  │ No         │ FPU error          │
│   17  │ #AC Alignment Check     │ Fault  │ Yes (0)    │ Unaligned access   │
│   18  │ #MC Machine Check       │ Abort  │ No         │ Hardware error     │
│   19  │ #XM SIMD Exception      │ Fault  │ No         │ SSE/AVX error      │
│   ────┴─────────────────────────┴────────┴────────────┴──────────────────  │
│   32-255: Available for external interrupts and software interrupts        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context and Further Reading

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HISTORICAL CONTEXT                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   EVOLUTION OF INTERRUPT HANDLING:                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1950s: Polling only - CPU continuously checks devices             │ │
│   │   1960s: Hardware interrupts invented                               │ │
│   │   1970s: Vectored interrupts, priority systems                      │ │
│   │   1980s: 8259 PIC becomes standard on IBM PC                        │ │
│   │   1990s: APIC for multiprocessor systems                            │ │
│   │   2000s: MSI/MSI-X for PCI Express                                  │ │
│   │   2010s: Posted interrupts for virtualization                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   FURTHER READING:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • "The Design of the UNIX Operating System" - Maurice Bach        │ │
│   │   • "Linux Kernel Development" - Robert Love                        │ │
│   │   • "Understanding the Linux Kernel" - Bovet & Cesati               │ │
│   │   • "Linux Device Drivers" - Corbet, Rubini, Kroah-Hartman          │ │
│   │   • Intel Software Developer's Manual, Vol. 3                       │ │
│   │   • Linux kernel source: kernel/irq/, arch/x86/kernel/              │ │
│   │   • Documentation/core-api/genericirq.rst in kernel tree            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Conclusion

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONCLUSION                                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Interrupts are the heartbeat of modern operating systems, enabling      │
│   efficient interaction between software and hardware without wasting     │
│   CPU cycles on polling.                                                  │
│                                                                            │
│   KEY TAKEAWAYS:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. Interrupts provide ASYNCHRONOUS event notification             │ │
│   │                                                                     │ │
│   │   2. Hardware has evolved from simple PIC to complex APIC/MSI-X     │ │
│   │                                                                     │ │
│   │   3. Handlers must be FAST - use top/bottom half split              │ │
│   │                                                                     │ │
│   │   4. Context matters - know what you can/cannot do in each context  │ │
│   │                                                                     │ │
│   │   5. Choose the right deferred mechanism:                           │ │
│   │      • Tasklet: Fast, atomic, no sleeping                           │ │
│   │      • Workqueue: Flexible, can sleep                               │ │
│   │      • Threaded IRQ: Best of both worlds                            │ │
│   │                                                                     │ │
│   │   6. Debug with /proc/interrupts, ftrace, and proper logging        │ │
│   │                                                                     │ │
│   │   7. Consider SMP: affinity, locking, and cache effects             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Understanding interrupts deeply is essential for:                        │
│   • Writing device drivers                                                │
│   • Debugging system performance issues                                   │
│   • Understanding kernel internals                                        │
│   • Building real-time systems                                            │
│                                                                            │
│   ═══════════════════════════════════════════════════════════════════════ │
│   "The interrupt mechanism is one of the most important features of       │
│    modern computer architecture, allowing the operating system to         │
│    respond to external events in a timely and efficient manner."          │
│                                        - Maurice Bach (paraphrased)       │
│   ═══════════════════════════════════════════════════════════════════════ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

*Document generated following the pedagogical style of Maurice Bach's*
*"The Design of the UNIX Operating System"*