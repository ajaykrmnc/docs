# Kernel Debug Print Statement Guide

This document covers the print statements, debug macros, and logging mechanisms used in the kernel code, along
with techniques to enable/disable them and prevent log flooding.

---

## Table of Contents

1. [Standard Kernel Print Functions](#standard-kernel-print-functions)
2. [Log Levels](#log-levels)
3. [pr\_\* Wrapper Macros](#pr_-wrapper-macros)
4. [Dynamic Debug (dyndbg)](#dynamic-debug-dyndbg)
5. [QDF Trace Framework (WLAN Drivers)](#qdf-trace-framework-wlan-drivers)
6. [Rate Limiting](#rate-limiting)
7. [Module-Specific Debug Controls](#module-specific-debug-controls)
8. [Preventing Log Flooding](#preventing-log-flooding)
9. [Console Log Level Control](#console-log-level-control)

---

## Standard Kernel Print Functions

### printk

The fundamental kernel print function:

```c
printk(KERN_INFO "Message with info level\n");
printk(KERN_ERR "Error message\n");
printk("Default level message\n");
```

---

## Log Levels

Kernel log levels (from highest to lowest priority):

| Level     | Macro          | Value | Description                      |
| --------- | -------------- | ----- | -------------------------------- |
| Emergency | `KERN_EMERG`   | 0     | System is unusable               |
| Alert     | `KERN_ALERT`   | 1     | Action must be taken immediately |
| Critical  | `KERN_CRIT`    | 2     | Critical conditions              |
| Error     | `KERN_ERR`     | 3     | Error conditions                 |
| Warning   | `KERN_WARNING` | 4     | Warning conditions               |
| Notice    | `KERN_NOTICE`  | 5     | Normal but significant           |
| Info      | `KERN_INFO`    | 6     | Informational                    |
| Debug     | `KERN_DEBUG`   | 7     | Debug-level messages             |

---

## pr\_\* Wrapper Macros

Preferred over raw `printk` - automatically prepends module name:

```c
pr_emerg("Emergency message\n");
pr_alert("Alert message\n");
pr_crit("Critical message\n");
pr_err("Error message\n");
pr_warn("Warning message\n");
pr_notice("Notice message\n");
pr_info("Informational message\n");
pr_debug("Debug message\n");      // Requires DEBUG or CONFIG_DYNAMIC_DEBUG
```

### Custom pr_fmt

Define at the top of your source file to customize prefix:

```c
#ifdef pr_fmt
#undef pr_fmt
#define pr_fmt(fmt) KBUILD_MODNAME ": %s: %d:" fmt, __func__, __LINE__
#endif
```

---

## Dynamic Debug (dyndbg)

When `CONFIG_DYNAMIC_DEBUG=y` is enabled (default in our builds), `pr_debug()` and `dev_dbg()` calls can be
enabled/disabled at runtime.

### Enabling Debug for a Module

```bash
# Enable all debug messages for a module
echo "module <module_name> +pmfl" > /sys/kernel/debug/dynamic_debug/control

# Disable all debug messages for a module
echo "module <module_name> -pmfl" > /sys/kernel/debug/dynamic_debug/control
```

### Flags Meaning

| Flag | Meaning                         |
| ---- | ------------------------------- |
| `p`  | Enable the pr_debug() callsite  |
| `m`  | Include module name in output   |
| `f`  | Include function name in output |
| `l`  | Include line number in output   |
| `t`  | Include thread ID in output     |

### Examples

```bash
# Enable debug for l2proxy module with function and line info
echo "module l2proxy +pmfl" > /sys/kernel/debug/dynamic_debug/control

# Enable debug for a specific file
echo "file my_driver.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable debug for a specific function
echo "func my_function +p" > /sys/kernel/debug/dynamic_debug/control

# View current debug settings
cat /sys/kernel/debug/dynamic_debug/control
```

---

## QDF Trace Framework (WLAN Drivers)

The QCA WLAN drivers use QDF (Qualcomm Driver Framework) for logging:

### QDF_TRACE Macro

```c
QDF_TRACE(QDF_MODULE_ID_DP, QDF_TRACE_LEVEL_DEBUG, "Debug message");
```

### Trace Levels

- `QDF_TRACE_LEVEL_NONE`
- `QDF_TRACE_LEVEL_FATAL`
- `QDF_TRACE_LEVEL_ERROR`
- `QDF_TRACE_LEVEL_WARN`
- `QDF_TRACE_LEVEL_INFO`
- `QDF_TRACE_LEVEL_INFO_HIGH`
- `QDF_TRACE_LEVEL_INFO_MED`
- `QDF_TRACE_LEVEL_INFO_LOW`
- `QDF_TRACE_LEVEL_DEBUG`

### Controlling QDF Debug Level

```bash
# Set qdf_dbg_mask via module parameter
echo <level> > /sys/module/qdf/parameters/qdf_dbg_mask
```

---

## Rate Limiting

### Using Rate-Limited Print Macros

```c
// Print only once
pr_info_once("This message prints only once\n");
pr_warn_once("Warning printed once\n");

// Rate-limited printing
if (printk_ratelimit())
  printk(KERN_INFO "Rate-limited message\n");

// Or use the rate-limited variants
pr_info_ratelimited("This is rate limited\n");
pr_err_ratelimited("Error with rate limiting\n");
```

### Custom Rate Limiting (used in WLAN drivers)
e

```c
#define DBGLOG_PRINT_RATE_LIMIT_PERIOD (2*HZ)  // 2 seconds
#define DBGLOG_PRINT_RATE_LIMIT_BURST_DEFAULT 250

DEFINE_RATELIMIT_STATE(dbglog_ratelimit, DBGLOG_PRINT_RATE_LIMIT_PERIOD,
                       DBGLOG_PRINT_RATE_LIMIT_BURST_DEFAULT);

if (__ratelimit(&dbglog_ratelimit)) {
  printk("Rate-limited debug message\n");
}
```

---

## Module-Specific Debug Controls

### Content Analytics Module

```bash
# Enable specific debug flags
echo <bitmask> > /sys/module/content_analytics/parameters/ca_debug_level

# Debug flags:
# DEBUG_SSID_APP_VIS    = (1 << 0) = 1
# DEBUG_CLIENT_APP_VIS  = (1 << 1) = 2
# DEBUG_WEB_QOE         = (1 << 2) = 4
# DEBUG_VOIP_QOE        = (1 << 3) = 8
```

### ACFG Debug Mask

```bash
# Set acfg_dbg_mask for WLAN driver debugging
# ACFG_DEBUG_FUNCTRACE = 0x01
# ACFG_DEBUG_LEVEL0    = 0x02
# ACFG_DEBUG_ERROR     = 0x20
# ACFG_DEBUG_CFG       = 0x40
```

---

## Preventing Log Flooding

### 1. Use Appropriate Log Level

Choose the right level for your message:

- Use `pr_debug()` for development/debugging (disabled by default)
- Use `pr_info()` sparingly for significant events
- Use `pr_err()` only for actual errors

### 2. Use Rate Limiting

```c
// For hot paths, always use rate limiting
pr_info_ratelimited("Packet processed: %d\n", count);
```

### 3. Use Conditional Compilation

```c
#ifdef DEBUG
pr_debug("Detailed debug info\n");
#endif
```

### 4. Use Debug Masks

```c
if (debug_level & MY_DEBUG_FLAG)
  pr_info("Conditional debug message\n");
```

---

## Console Log Level Control

### View Current Console Log Level

```bash
cat /proc/sys/kernel/printk
# Output: current default minimum boot-time-default
# Example: 7    4    1    7
```

### Change Console Log Level

```bash
# Set console log level (0-7, lower = more critical only)
echo 4 > /proc/sys/kernel/printk

# Or use dmesg
dmesg -n 4    # Show only warnings and above on console
```

### Kernel Config Options

Our builds typically use:

```
CONFIG_PRINTK_TIME=y           # Timestamp in logs
CONFIG_MESSAGE_LOGLEVEL_DEFAULT=4   # Default message level
CONFIG_CONSOLE_LOGLEVEL_DEFAULT=7   # Default console level
CONFIG_DYNAMIC_DEBUG=y         # Enable dynamic debug
```

---

## Quick Reference: Arista Module Debug

| Module            | Debug Control                                                            |
| ----------------- | ------------------------------------------------------------------------ |
| l2proxy           | `echo "module l2proxy +pmfl" > /sys/kernel/debug/dynamic_debug/control`  |
| content_analytics | `echo &lt;level&gt; > /sys/module/content_analytics/parameters/ca_debug_level` |
| ar (WLAN)         | Uses `ar_os_pr_debug()`, controlled via dyndbg                           |
| QCA WLAN          | `qdf_dbg_mask` module parameter                                          |

---

## Best Practices

1. **Always use `pr_*` macros** instead of raw `printk`
2. **Use `pr_debug()`** for development - it compiles out or can be toggled
3. **Rate-limit** any message that could be triggered frequently
4. **Use debug masks** for fine-grained control in complex modules
5. **Test with debug disabled** before committing code
6. **Use `_once` variants** for one-time notifications
