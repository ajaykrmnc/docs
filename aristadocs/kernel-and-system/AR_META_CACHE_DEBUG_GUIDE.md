# AR Meta Cache Kernel Patch - Debug Guide

## Overview

This document explains how to verify that the `ar_meta_cache.patch` is working correctly and how to check kernel debug messages on the AP device.

## Patch Details

**Patch File:** `ap/platform/patches/kernel/5.4/12.5/common/ar_meta_cache.patch`

**What it adds:**

- Adds `ar_meta` structure to `sk_buff` in `include/linux/skbuff.h`
- Initializes `ar_meta.tid` and `ar_meta.reserve` fields in `net/core/skbuff.c`
- Clears fields in `net/core/skbuff_recycle.c`
- Prints boot message: `sk_buff ar_meta support enabled (tid: 8-bit, reserve: 8-bit)`

---

## Test Environment Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           YOUR WORKSTATION                                │
│                     (where you develop/build kernel)                      │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ SSH
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         RASPBERRY PI (10.87.127.66)                       │
│                                                                           │
│  Role: Jump host / Serial console access                                  │
│  Logs: /var/log/kern.log (Pi's OWN kernel logs - NOT your patch!)        │
│                                                                           │
│  Connected to AP via:                                                     │
│    - Serial: /dev/ttyUSB7 (use tio)                                      │
│    - Network: SSH to 10.87.118.59                                        │
└──────────────────────────────────────────────────────────────────────────┘
                          │                    │
              Serial Console              SSH/Network
              /dev/ttyUSB7                     │
                          │                    │
                          ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         AP DEVICE (10.87.118.59)                          │
│                                                                           │
│  Role: Target device running YOUR PATCHED KERNEL                          │
│  Credentials: root / arastra                                              │
│  Logs: /var/log/kern.logs (YOUR PATCH LOGS ARE HERE!) ✅                  │
│                                                                           │
│  This is where sk_buff changes run!                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## When to Check Which Device?

| What You Want              | Check This Device               | Log Location         |
| -------------------------- | ------------------------------- | -------------------- |
| Your kernel patch logs     | **AP Device** (10.87.118.59)    | `/var/log/kern.logs` |
| sk_buff / ar_meta messages | **AP Device** (10.87.118.59)    | `/var/log/kern.logs` |
| Serial console issues      | **Raspberry Pi** (10.87.127.66) | `/var/log/messages`  |
| tio/USB connection issues  | **Raspberry Pi** (10.87.127.66) | `/var/log/kern.log`  |
| Pi's own kernel issues     | **Raspberry Pi** (10.87.127.66) | `/var/log/kern.log`  |

### Common Mistake ❌

```bash
# WRONG - This checks Raspberry Pi's kernel, not your patched AP kernel!
pi@raspberrypi:~ $ grep ar_meta /var/log/kern.log
# (empty - because Pi doesn't have your patch)
```

### Correct Way ✅

```bash
# RIGHT - Check on the AP device
pi@raspberrypi:~ $ ssh root@10.87.118.59 "grep ar_meta /var/log/kern.logs"
# Shows your patch message!
```

---

## Understanding dmesg and Kernel Log Levels

### What is dmesg?

`dmesg` displays the kernel ring buffer - a fixed-size circular buffer in RAM that stores kernel messages.

### Kernel Log Levels (0-7)

| Level | Name         | Macro         | Description                             |
| ----- | ------------ | ------------- | --------------------------------------- |
| 0     | KERN_EMERG   | `pr_emerg()`  | System is unusable                      |
| 1     | KERN_ALERT   | `pr_alert()`  | Action must be taken immediately        |
| 2     | KERN_CRIT    | `pr_crit()`   | Critical conditions                     |
| 3     | KERN_ERR     | `pr_err()`    | Error conditions                        |
| 4     | KERN_WARNING | `pr_warn()`   | Warning conditions                      |
| 5     | KERN_NOTICE  | `pr_notice()` | Normal but significant                  |
| 6     | KERN_INFO    | `pr_info()`   | Informational ✅ (your patch uses this) |
| 7     | KERN_DEBUG   | `pr_debug()`  | Debug-level messages                    |

### Check Current Console Log Level

```bash
# On AP device:
cat /proc/sys/kernel/printk
# Output: 7    4    1    7
#         │    │    │    └── boot-time default
#         │    │    └─────── minimum console level
#         │    └──────────── default message level
#         └───────────────── current console level (messages < this are shown)
```

### Enable All Log Levels (including debug)

```bash
# On AP device - show all messages including debug (level 7)
echo 8 > /proc/sys/kernel/printk

# Or use dmesg
dmesg -n 8
```

---

## Log Storage Locations on AP Device

| Location             | What's Stored          | Persistent?                  | When to Use                   |
| -------------------- | ---------------------- | ---------------------------- | ----------------------------- |
| `dmesg`              | Kernel ring buffer     | ❌ No (RAM only, overwrites) | Recent kernel messages        |
| `/var/log/kern.logs` | All kernel messages    | ✅ Yes                       | **Boot messages, your patch** |
| `/var/log/messages`  | System/daemon messages | ✅ Yes                       | Application logs              |
| `/var/log/app.logs`  | Application logs       | ✅ Yes                       | AP application debugging      |

### Why dmesg Loses Early Boot Messages

```
Boot Timeline:
──────────────────────────────────────────────────────────────────────────▶
│                                                                          │
│  0s: Kernel starts                                                       │
│      └── skb_init() runs                                                 │
│          └── pr_info("sk_buff ar_meta support enabled...")  ◄── YOUR MSG │
│                                                                          │
│  ~200s: Many kernel messages later...                                    │
│         └── Ring buffer is FULL                                          │
│             └── Early messages OVERWRITTEN                               │
│                                                                          │
│  Now: You run dmesg                                                      │
│       └── Only sees recent ~35 messages                                  │
│           └── Your boot message is GONE from dmesg                       │
│                                                                          │
│  BUT: /var/log/kern.logs has ALL messages saved to disk ✅               │
──────────────────────────────────────────────────────────────────────────▶
```

---

## How to Detect sk_buff Changes

### Method 1: Check Boot Log Message (Recommended)

```bash
# From Raspberry Pi - one liner:
ssh root@10.87.118.59 "grep -i 'sk_buff\|ar_meta' /var/log/kern.logs"

# Expected output:
# 2026-01-26T10:18:12.971877+00:00 kern.info kernel: skbuff: sk_buff ar_meta support enabled (tid: 8-bit, reserve: 8-bit)
```

### Method 2: Verify Kernel Build Timestamp

```bash
ssh root@10.87.118.59 "uname -a"
# Check the build date matches when you compiled the patched kernel
# Example: Mon Jan 26 06:09:38 UTC 2026
```

### Method 3: Check sk_buff Size (Advanced)

```bash
# On AP device - check structure size via /proc or debug info
ssh root@10.87.118.59 "cat /proc/slabinfo | grep skbuff"
```

### Method 4: Live Boot Capture via Serial Console

```bash
# On Raspberry Pi - capture entire boot sequence:
tio /dev/ttyUSB7 --log --log-file /tmp/ap_boot.log

# In another terminal, reboot the AP:
ssh root@10.87.118.59 "reboot"

# Watch the boot messages scroll by in tio
# All messages saved to /tmp/ap_boot.log

# After boot, search the captured log:
grep -i "sk_buff\|ar_meta" /tmp/ap_boot.log
```

### Method 5: Watch dmesg in Real-Time

```bash
# On AP device (useful for runtime messages, not boot):
dmesg -w

# Or follow kern.logs:
tail -f /var/log/kern.logs
```

---

## Step-by-Step Verification Workflow

### After Flashing New Kernel to AP:

```bash
# Step 1: Connect to Raspberry Pi
ssh pi@10.87.127.66

# Step 2: Start serial console with logging
tio /dev/ttyUSB7 --log --log-file /tmp/boot.log

# Step 3: (In another terminal) Reboot AP
ssh root@10.87.118.59 "reboot"

# Step 4: Watch boot messages in tio window
# Look for: "sk_buff ar_meta support enabled"

# Step 5: After boot completes, verify via SSH
ssh root@10.87.118.59 "grep sk_buff /var/log/kern.logs"

# Step 6: Confirm kernel version
ssh root@10.87.118.59 "uname -a"
```

---

## Enabling pr_debug Messages

If you use `pr_debug()` instead of `pr_info()`, messages are compiled out by default. Enable them:

### Runtime Enable (Dynamic Debug)

```bash
# On AP device:

# 1. Set console to show debug level
echo 8 > /proc/sys/kernel/printk

# 2. Enable debug for specific file
echo 'file skbuff.c +p' > /sys/kernel/debug/dynamic_debug/control

# 3. Enable debug for specific function
echo 'func skb_init +p' > /sys/kernel/debug/dynamic_debug/control

# 4. Enable all debug in a module
echo 'module skbuff +p' > /sys/kernel/debug/dynamic_debug/control

# 5. View what's enabled
cat /sys/kernel/debug/dynamic_debug/control | grep skbuff
```

### Boot-time Enable (Kernel Command Line)

Add to bootloader (U-Boot):

```bash
setenv bootargs ${bootargs} loglevel=8 debug dyndbg="file skbuff.c +p"
boot
```

---

## Quick Reference Commands

### From Raspberry Pi:

```bash
# Check AP kernel logs (your patch)
ssh root@10.87.118.59 "grep sk_buff /var/log/kern.logs"

# Check AP kernel version
ssh root@10.87.118.59 "uname -a"

# Check AP dmesg (recent messages only)
ssh root@10.87.118.59 "dmesg | tail -50"

# Connect to AP serial console
tio /dev/ttyUSB7

# Capture boot with logging
tio /dev/ttyUSB7 --log --log-file boot.log
```

### On AP Device (after SSH or serial):

```bash
# Find your patch message
grep -i "ar_meta\|sk_buff" /var/log/kern.logs

# Check all kernel logs
cat /var/log/kern.logs

# Watch live kernel messages
dmesg -w
tail -f /var/log/kern.logs

# Check log level
cat /proc/sys/kernel/printk

# Enable debug messages
echo 8 > /proc/sys/kernel/printk
```

---

## Troubleshooting

| Problem                 | Cause                   | Solution                        |
| ----------------------- | ----------------------- | ------------------------------- |
| No output from `dmesg`  | Ring buffer overwritten | Use `/var/log/kern.logs`        |
| Checking wrong device   | On Pi instead of AP     | SSH to 10.87.118.59 first       |
| Message not found       | Old kernel running      | Check `uname -a` for build time |
| `pr_debug` not printing | Debug disabled          | Enable dynamic debug            |
| Serial console blank    | Wrong USB port          | Check `ls /dev/ttyUSB*`         |
| SSH connection refused  | AP not booted           | Wait or check serial console    |

---

## Summary

1. **Your patch logs are on the AP device** (10.87.118.59), not the Raspberry Pi
2. **Use `/var/log/kern.logs`** for boot messages (dmesg loses them)
3. **Use `pr_info()`** for messages you always want to see
4. **Use `pr_debug()`** for verbose debugging (requires dynamic debug enable)
5. **Capture boot logs** with `tio --log` for complete boot analysis
