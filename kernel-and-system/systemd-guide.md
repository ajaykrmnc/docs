# Comprehensive Guide to systemd

## Table of Contents

1. [Introduction](#introduction)
2. [History and Background](#history-and-background)
3. [Core Architecture](#core-architecture)
4. [Unit Types](#unit-types)
5. [Unit File Structure](#unit-file-structure)
6. [systemctl Commands](#systemctl-commands)
7. [Service Management](#service-management)
8. [Targets and Runlevels](#targets-and-runlevels)
9. [Timers](#timers)
10. [Socket Activation](#socket-activation)
11. [journald and Logging](#journald-and-logging)
12. [Resource Control with cgroups](#resource-control-with-cgroups)
13. [systemd-networkd](#systemd-networkd)
14. [Boot Process](#boot-process)
15. [Security Features](#security-features)
16. [Best Practices](#best-practices)
17. [Troubleshooting](#troubleshooting)
18. [Advanced Topics](#advanced-topics)

---

## Introduction

**systemd** is a suite of basic building blocks for a Linux system. It provides a system and service manager 
that runs as PID 1 and starts the rest of the system. systemd provides aggressive parallelization 
capabilities, uses socket and D-Bus activation for starting services, offers on-demand starting of daemons, 
keeps track of processes using Linux control groups, maintains mount and automount points, and implements an 
elaborate transactional dependency-based service control logic.

### Key Features

- **Parallelized service startup** - Services start in parallel, reducing boot time
- **On-demand activation** - Services can be started when needed via socket, bus, path, or timer activation
- **Process tracking** - Uses cgroups to track processes, ensuring clean service stops
- **Snapshot and restore** - System state can be saved and restored
- **Mount handling** - Manages mount points and can automount
- **Dependency-based control** - Sophisticated dependency system between units
- **Logging integration** - Integrated logging via journald
- **Login management** - Manages user logins via systemd-logind

---

## History and Background

### Timeline

| Year | Event |
|------|-------|
| 2010 | Lennart Poettering and Kay Sievers announce systemd |
| 2011 | Fedora 15 becomes the first major distribution to adopt systemd |
| 2012 | openSUSE and Arch Linux adopt systemd |
| 2014 | Debian adopts systemd after controversial vote |
| 2015 | Ubuntu switches from Upstart to systemd |
| Present | systemd is the default init system for most major Linux distributions |

### Predecessors

- **SysV init** - Traditional Unix init system using shell scripts
- **Upstart** - Event-based init system developed by Ubuntu
- **OpenRC** - Dependency-based init system (still used by Gentoo)

### Design Philosophy

systemd was designed to:
1. Start services in parallel to reduce boot time
2. Track processes using cgroups instead of PIDs
3. Provide consistent management interface across distributions
4. Integrate tightly with the Linux kernel features
5. Replace multiple standalone utilities with unified components

---

## Core Architecture

### Main Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         systemd Suite                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   systemd   │  │  journald   │  │   logind    │             │
│  │  (PID 1)    │  │  (logging)  │  │  (sessions) │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  networkd   │  │  resolved   │  │  timesyncd  │             │
│  │ (networking)│  │    (DNS)    │  │   (NTP)     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    udevd    │  │  hostnamed  │  │  localed    │             │
│  │  (devices)  │  │ (hostname)  │  │  (locale)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component | Binary | Purpose |
|-----------|--------|---------|
| systemd | systemd | Main init system and service manager |
| journald | systemd-journald | Logging daemon |
| logind | systemd-logind | Login and session manager |
| networkd | systemd-networkd | Network configuration |
| resolved | systemd-resolved | DNS resolver |
| timesyncd | systemd-timesyncd | NTP client |
| udevd | systemd-udevd | Device manager |
| hostnamed | systemd-hostnamed | Hostname management |
| localed | systemd-localed | Locale management |
| timedated | systemd-timedated | Time and date management |
| machined | systemd-machined | Container/VM management |

---

## Unit Types

systemd manages **units**, which are resources that systemd knows how to manage. There are several unit types:

### Overview of Unit Types

| Unit Type | Extension | Description |
|-----------|-----------|-------------|
| Service | `.service` | System services (daemons) |
| Socket | `.socket` | IPC or network sockets for socket activation |
| Target | `.target` | Groups of units (similar to runlevels) |
| Device | `.device` | Kernel device exposed in udev |
| Mount | `.mount` | Filesystem mount point |
| Automount | `.automount` | Automount point for on-demand mounting |
| Swap | `.swap` | Swap device or file |
| Path | `.path` | Path-based activation |
| Timer | `.timer` | Timer-based activation (cron replacement) |
| Slice | `.slice` | cgroup slice for resource management |
| Scope | `.scope` | Externally created process group |
| Snapshot | `.snapshot` | Saved state of systemd manager |

### Service Units (.service)

Service units are the most common type. They control daemons and processes.

```ini
[Unit]
Description=My Custom Service
Documentation=https://example.com/docs
After=network.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/my-service
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
Restart=on-failure
RestartSec=5
User=myuser
Group=mygroup

[Install]
WantedBy=multi-user.target
```

### Socket Units (.socket)

Socket units enable socket-based activation:

```ini
[Unit]
Description=My Socket

[Socket]
ListenStream=/run/my-service.sock
ListenStream=8080
Accept=no

[Install]
WantedBy=sockets.target
```

### Timer Units (.timer)

Timer units provide cron-like functionality:

```ini
[Unit]
Description=Run my script daily

[Timer]
OnCalendar=daily
Persistent=true
Unit=my-script.service

[Install]
WantedBy=timers.target
```

### Path Units (.path)

Path units monitor filesystem changes:

```ini
[Unit]
Description=Watch /etc/config for changes

[Path]
PathChanged=/etc/config
Unit=config-reload.service

[Install]
WantedBy=multi-user.target
```

### Mount Units (.mount)

Mount units control mount points (unit name must match mount path with `/` replaced by `-`):

```ini
[Unit]
Description=Mount Data Disk

[Mount]
What=/dev/sdb1
Where=/data
Type=ext4
Options=defaults

[Install]
WantedBy=multi-user.target
```

---

## Unit File Structure

### Unit File Locations

systemd looks for unit files in several locations, with different priorities:

| Priority | Location | Description |
|----------|----------|-------------|
| Highest | `/etc/systemd/system/` | Local configuration (admin) |
| Medium | `/run/systemd/system/` | Runtime units |
| Lower | `/usr/lib/systemd/system/` | Distribution-provided units |
| Lowest | `/lib/systemd/system/` | Legacy location |

**Note:** Higher priority locations override lower ones.

### Unit File Sections

Every unit file can have these common sections:

#### [Unit] Section

```ini
[Unit]
# Basic description
Description=Apache Web Server
Documentation=man:httpd(8) https://httpd.apache.org/docs/

# Dependencies
Requires=network.target          # Hard dependency
Wants=network-online.target      # Soft dependency
BindsTo=other.service            # Like Requires, but also stops when other stops
PartOf=other.service             # Start/stop together
Conflicts=other.service          # Cannot run together

# Ordering (does not imply dependency)
Before=other.service             # Start before other
After=network.target             # Start after network

# Conditions and Assertions
ConditionPathExists=/etc/httpd/conf/httpd.conf
ConditionPathIsDirectory=/var/www
AssertArchitecture=x86-64

# Failure handling
OnFailure=failure-handler.service
OnSuccess=success-handler.service

# Other
RefuseManualStart=no
RefuseManualStop=no
AllowIsolate=no
DefaultDependencies=yes
```

#### [Install] Section

```ini
[Install]
# Targets that should include this unit
WantedBy=multi-user.target
RequiredBy=graphical.target

# Aliases for this unit
Alias=webserver.service

# Additional units to enable together
Also=httpd-helper.service

# Default instance for template units
DefaultInstance=main
```

---

## systemctl Commands

`systemctl` is the primary command for managing systemd. Here's a comprehensive reference:

### Basic Service Management

```bash
# Start a service
systemctl start nginx.service

# Stop a service
systemctl stop nginx.service

# Restart a service (stop then start)
systemctl restart nginx.service

# Reload configuration without full restart
systemctl reload nginx.service

# Reload or restart (reload if supported, otherwise restart)
systemctl reload-or-restart nginx.service

# Check service status
systemctl status nginx.service

# Check if service is active
systemctl is-active nginx.service

# Check if service is enabled
systemctl is-enabled nginx.service

# Check if service failed
systemctl is-failed nginx.service
```

### Enable/Disable Services

```bash
# Enable service to start at boot
systemctl enable nginx.service

# Disable service from starting at boot
systemctl disable nginx.service

# Enable and start immediately
systemctl enable --now nginx.service

# Disable and stop immediately
systemctl disable --now nginx.service

# Re-enable (disable then enable)
systemctl reenable nginx.service

# Prevent service from being started (even manually)
systemctl mask nginx.service

# Remove mask
systemctl unmask nginx.service
```

### Listing Units

```bash
# List all loaded units
systemctl list-units

# List all units (including inactive)
systemctl list-units --all

# List only service units
systemctl list-units --type=service

# List failed units
systemctl list-units --failed

# List unit files
systemctl list-unit-files

# List dependencies
systemctl list-dependencies nginx.service

# List reverse dependencies (what depends on this)
systemctl list-dependencies --reverse nginx.service
```

### System State Commands

```bash
# Reboot the system
systemctl reboot

# Power off
systemctl poweroff

# Suspend
systemctl suspend

# Hibernate
systemctl hibernate

# Hybrid sleep (suspend + hibernate)
systemctl hybrid-sleep

# Halt
systemctl halt

# Emergency mode
systemctl emergency

# Rescue mode (single-user)
systemctl rescue
```

### Target Management

```bash
# Get default target
systemctl get-default

# Set default target
systemctl set-default multi-user.target

# Switch to a target (like changing runlevel)
systemctl isolate graphical.target

# List all targets
systemctl list-units --type=target
```

### Daemon Management

```bash
# Reload systemd manager configuration
systemctl daemon-reload

# Re-execute systemd manager
systemctl daemon-reexec

# Reset failed state of units
systemctl reset-failed

# Reset failed state for specific unit
systemctl reset-failed nginx.service
```

### Viewing Unit Configuration

```bash
# Show unit file content
systemctl cat nginx.service

# Show unit properties
systemctl show nginx.service

# Show specific property
systemctl show nginx.service -p MainPID

# Edit unit file (creates override)
systemctl edit nginx.service

# Edit full unit file
systemctl edit --full nginx.service

# Show all overrides
systemd-delta
```

---

## Service Management

### Service Types

The `Type=` directive in the `[Service]` section defines how systemd determines when a service has started:

| Type | Description | Use Case |
|------|-------------|----------|
| `simple` | Default. Process specified in ExecStart is the main process | Most services |
| `exec` | Like simple, but service is "started" after ExecStart binary is executed | Services that may fail 
immediately |
| `forking` | Service forks; parent exits, child becomes main process | Traditional daemons |
| `oneshot` | Process exits after doing its work | Setup scripts |
| `dbus` | Service acquires a D-Bus name | D-Bus services |
| `notify` | Service sends notification via sd_notify() | Modern daemons |
| `idle` | Like simple, but waits for all jobs to complete | Services that shouldn't delay boot |

### Service Type Examples

#### simple (default)
```ini
[Service]
Type=simple
ExecStart=/usr/bin/my-simple-daemon
```

#### forking
```ini
[Service]
Type=forking
PIDFile=/var/run/my-daemon.pid
ExecStart=/usr/bin/my-daemon --daemon
```

#### oneshot
```ini
[Service]
Type=oneshot
ExecStart=/usr/bin/setup-script.sh
RemainAfterExit=yes
```

#### notify
```ini
[Service]
Type=notify
ExecStart=/usr/bin/my-notify-daemon
NotifyAccess=main
```

### Restart Policies

| Option | Description |
|--------|-------------|
| `no` | Don't restart (default) |
| `on-success` | Restart only if clean exit (exit code 0) |
| `on-failure` | Restart if unclean exit, signal, or timeout |
| `on-abnormal` | Restart if signal or timeout |
| `on-abort` | Restart only if signal |
| `on-watchdog` | Restart only if watchdog timeout |
| `always` | Always restart |

```ini
[Service]
Restart=on-failure
RestartSec=5
RestartPreventExitStatus=23
RestartForceExitStatus=SIGTERM
```

### Limiting Restarts

```ini
[Service]
Restart=always
RestartSec=5

# Limit restart bursts
StartLimitIntervalSec=500
StartLimitBurst=5

# Action when limit exceeded
StartLimitAction=reboot-force
```

### Exec Options

```ini
[Service]
# Main commands
ExecStartPre=/usr/bin/pre-start.sh      # Run before ExecStart
ExecStart=/usr/bin/my-service            # Main start command
ExecStartPost=/usr/bin/post-start.sh    # Run after ExecStart
ExecReload=/bin/kill -HUP $MAINPID      # Reload command
ExecStop=/usr/bin/graceful-stop.sh       # Stop command
ExecStopPost=/usr/bin/cleanup.sh         # Run after stop

# Prefix modifiers
ExecStart=-/usr/bin/may-fail             # - ignores failure
ExecStart=+/usr/bin/needs-root           # + runs as root
ExecStart=!/usr/bin/no-env               # ! clears environment
ExecStart=!!/usr/bin/no-env-full         # !! even more env clearing
```

### Environment Variables

```ini
[Service]
# Set environment variables
Environment="VAR1=value1" "VAR2=value2"

# Load from file
EnvironmentFile=/etc/default/my-service
EnvironmentFile=-/etc/default/optional-file  # - means optional

# Pass specific env vars
PassEnvironment=HOME USER

# Unset specific env vars
UnsetEnvironment=SECRET_VAR
```

### Working Directory and User

```ini
[Service]
# Working directory
WorkingDirectory=/opt/my-app
WorkingDirectory=~                        # User's home directory

# User and group
User=myuser
Group=mygroup

# Supplementary groups
SupplementaryGroups=docker audio

# Dynamic user (creates temporary user)
DynamicUser=yes
```

---

## Targets and Runlevels

### What are Targets?

Targets are groups of units that represent system states. They replace the traditional SysV runlevels.

### Target to Runlevel Mapping

| Runlevel | Target | Description |
|----------|--------|-------------|
| 0 | poweroff.target | System halt |
| 1, S | rescue.target | Single-user mode |
| 2, 3, 4 | multi-user.target | Multi-user, text mode |
| 5 | graphical.target | Multi-user, graphical |
| 6 | reboot.target | System reboot |
| emergency | emergency.target | Emergency shell |

### Important Targets

```bash
# Common targets
default.target          # Default boot target (usually symlink)
multi-user.target       # Full multi-user system
graphical.target        # Multi-user with GUI
rescue.target           # Single-user rescue mode
emergency.target        # Minimal emergency shell

# Startup targets
sysinit.target          # System initialization
basic.target            # Basic system (after sysinit)
network.target          # Network configuration started
network-online.target   # Network is actually online

# Hardware targets
sound.target            # Sound stack ready
bluetooth.target        # Bluetooth stack ready
printer.target          # Printer stack ready

# Special targets
hibernate.target        # System hibernation
suspend.target          # System suspend
sleep.target            # Any sleep state
```

### Working with Targets

```bash
# Get current default target
systemctl get-default

# Set default target
systemctl set-default graphical.target

# Change to different target
systemctl isolate multi-user.target

# See what units are in a target
systemctl list-dependencies graphical.target

# Create custom target
cat > /etc/systemd/system/my-custom.target << EOF
[Unit]
Description=My Custom Target
Requires=multi-user.target
After=multi-user.target
AllowIsolate=yes
EOF
```

### Target Dependencies

```
┌──────────────┐
│   default    │
│   target     │
└──────┬───────┘
│
┌────────────┴────────────┐
▼                         ▼
┌───────────────┐       ┌─────────────────┐
│ multi-user    │       │  graphical      │
│   target      │       │   target        │
└───────┬───────┘       └─────────────────┘
│
┌───────┴───────┐
▼               ▼
┌─────────────┐  ┌─────────────┐
│   basic     │  │   network   │
│  target     │  │   target    │
└──────┬──────┘  └─────────────┘
│
▼
┌─────────────┐
│  sysinit    │
│  target     │
└──────┬──────┘
│
▼
┌─────────────┐
│   local-fs  │
│   target    │
└─────────────┘
```

---

## Timers

systemd timers are a powerful replacement for cron. They offer more flexibility and better integration with 
the system.

### Timer vs Cron Comparison

| Feature | Cron | systemd Timer |
|---------|------|---------------|
| Dependency handling | No | Yes |
| Calendar expressions | Limited | Powerful |
| Randomized delays | No | Yes |
| Persistent across reboots | No | Yes |
| Resource control | No | Yes |
| Logging | Basic | Full journald |
| Wake from suspend | No | Yes |

### Timer Types

#### Monotonic Timers
Triggered relative to various events:

```ini
[Timer]
OnActiveSec=5m              # After timer unit is activated
OnBootSec=15m               # After boot
OnStartupSec=10m            # After systemd started
OnUnitActiveSec=1h          # After the service was last activated
OnUnitInactiveSec=30m       # After the service became inactive
```

#### Calendar Timers
Triggered at specific times:

```ini
[Timer]
OnCalendar=*-*-* 02:00:00   # Every day at 2 AM
OnCalendar=Mon *-*-* 00:00:00  # Every Monday midnight
OnCalendar=*-*-01 00:00:00  # First of every month
OnCalendar=hourly           # Every hour
OnCalendar=daily            # Every day at midnight
OnCalendar=weekly           # Every Monday at midnight
OnCalendar=monthly          # First of month
OnCalendar=yearly           # January 1st
```

### Calendar Expression Examples

```bash
# Every 5 minutes
OnCalendar=*:0/5

# Every 15 minutes from 9 AM to 5 PM on weekdays
OnCalendar=Mon..Fri 9..17:0/15

# Every Saturday and Sunday at 10:30 AM
OnCalendar=Sat,Sun *-*-* 10:30:00

# Last day of every month
OnCalendar=*-*~01 00:00:00

# Second Tuesday of every month
OnCalendar=Tue *-*-8..14 00:00:00

# Test calendar expressions
systemd-analyze calendar "Mon *-*-* 00:00:00"
systemd-analyze calendar "daily" --iterations=5
```

### Complete Timer Example

**mytask.timer:**
```ini
[Unit]
Description=Run My Task Every Hour

[Timer]
OnCalendar=hourly
RandomizedDelaySec=10m
Persistent=true
Unit=mytask.service

[Install]
WantedBy=timers.target
```

**mytask.service:**
```ini
[Unit]
Description=My Scheduled Task

[Service]
Type=oneshot
ExecStart=/usr/local/bin/my-task.sh
User=taskuser
```

### Timer Options

```ini
[Timer]
# Accuracy (default 1 minute)
AccuracySec=1s

# Add random delay (for spreading load)
RandomizedDelaySec=1h

# Run immediately if timer was missed (e.g., system was off)
Persistent=true

# Which service to trigger (defaults to same name .service)
Unit=my-actual-service.service

# Wake system from suspend to run
WakeSystem=true

# Remain after all timers elapse
RemainAfterElapse=yes
```

### Managing Timers

```bash
# List all timers
systemctl list-timers

# List all timers including inactive
systemctl list-timers --all

# Enable and start a timer
systemctl enable --now mytask.timer

# Check timer status
systemctl status mytask.timer

# Manually trigger the associated service
systemctl start mytask.service

# View timer logs
journalctl -u mytask.timer
journalctl -u mytask.service
```

---

## Socket Activation

Socket activation allows systemd to create sockets on behalf of services, starting the service only when a 
connection is made.

### Benefits of Socket Activation

1. **Faster boot** - Services start only when needed
2. **On-demand** - Resources used only when required
3. **Automatic restart** - If service crashes, socket remains; new connection restarts service
4. **Parallelization** - Services can be started simultaneously without dependency ordering
5. **Buffer connections** - systemd buffers connections while service starts

### Socket Types

```ini
[Socket]
# TCP socket
ListenStream=8080
ListenStream=127.0.0.1:8080
ListenStream=[::1]:8080

# UDP socket
ListenDatagram=514

# Unix socket (stream)
ListenStream=/run/myservice.sock

# Unix socket (datagram)
ListenDatagram=/run/myservice.sock

# Sequential packet socket
ListenSequentialPacket=/run/myservice.sock

# FIFO (named pipe)
ListenFIFO=/run/myservice.fifo

# Message queue
ListenMessageQueue=/myqueue

# USB function FS
ListenUSBFunction=/dev/usb-ffs/adb/ep0
```

### Socket Activation Example

**myapp.socket:**
```ini
[Unit]
Description=My Application Socket

[Socket]
ListenStream=/run/myapp.sock
ListenStream=8080
SocketMode=0660
SocketUser=www-data
SocketGroup=www-data

# Accept connections in service (not inetd-style)
Accept=no

# Service to activate
Service=myapp.service

[Install]
WantedBy=sockets.target
```

**myapp.service:**
```ini
[Unit]
Description=My Application
Requires=myapp.socket

[Service]
Type=simple
ExecStart=/usr/bin/myapp
# Receive sockets via systemd
StandardInput=socket

# For services that expect file descriptors
Environment="LISTEN_FDS=1"
```

### Accept Mode

The `Accept=` option determines how connections are handled:

| Accept | Behavior | Use Case |
|--------|----------|----------|
| `no` | One service instance handles all connections | Modern services |
| `yes` | New service instance per connection (inetd-style) | Simple scripts |

**Accept=yes example:**
```ini
[Socket]
Accept=yes
ListenStream=8080

# For inetd-style, use @ in service name
# myapp@.service will be instantiated as myapp@<connection-id>.service
```

### Socket Options

```ini
[Socket]
# Socket permissions
SocketMode=0660
SocketUser=myuser
SocketGroup=mygroup

# Directory permissions (for Unix sockets)
DirectoryMode=0755

# Connection handling
MaxConnections=64
MaxConnectionsPerSource=8
KeepAlive=true
KeepAliveTimeSec=300

# Buffer sizes
ReceiveBuffer=64K
SendBuffer=64K

# Socket options
NoDelay=true
Priority=10
ReusePort=true
Transparent=true

# Bind restrictions
FreeBind=true
BindIPv6Only=both
```

### Socket Commands

```bash
# List all sockets
systemctl list-sockets

# Start socket (not service)
systemctl start myapp.socket

# Check socket status
systemctl status myapp.socket

# Stop socket (will also stop service)
systemctl stop myapp.socket

# Test socket activation
systemd-socket-activate -l 8080 /usr/bin/myapp
```

---

## journald and Logging

systemd includes `journald`, a system service that collects and stores logging data in a structured, indexed 
binary format.

### journald Features

- **Structured logging** - Logs stored with metadata
- **Indexed** - Fast searching
- **Compressed** - Efficient storage
- **Secure** - Tamper-evident sealing (optional)
- **Integrated** - Captures stdout/stderr from services
- **Forward sealing** - Detects log tampering

### journalctl Basic Usage

```bash
# View all logs
journalctl

# Follow logs in real-time (like tail -f)
journalctl -f

# Show only kernel messages
journalctl -k
journalctl --dmesg

# Show logs from current boot
journalctl -b

# Show logs from previous boot
journalctl -b -1

# List boots
journalctl --list-boots

# Show newest entries first
journalctl -r
journalctl --reverse
```

### Filtering Logs

```bash
# By unit
journalctl -u nginx.service
journalctl -u nginx.service -u php-fpm.service

# By priority (0=emerg to 7=debug)
journalctl -p err        # error and above
journalctl -p warning    # warning and above
journalctl -p 0..4       # range

# By time
journalctl --since "2024-01-15"
journalctl --since "2024-01-15 10:00:00"
journalctl --since "1 hour ago"
journalctl --since yesterday
journalctl --since "2024-01-15" --until "2024-01-16"

# By PID, UID, GID
journalctl _PID=1234
journalctl _UID=1000
journalctl _GID=100

# By executable
journalctl /usr/bin/nginx
journalctl _COMM=nginx

# By systemd unit (alternative syntax)
journalctl _SYSTEMD_UNIT=nginx.service

# By hostname
journalctl _HOSTNAME=myserver
```

### Output Formats

```bash
# Short (default)
journalctl -o short

# Verbose (all fields)
journalctl -o verbose

# JSON
journalctl -o json
journalctl -o json-pretty

# Export format (for backup)
journalctl -o export

# Cat (just message)
journalctl -o cat

# With timestamps
journalctl -o short-iso
journalctl -o short-precise
journalctl -o short-unix
```

### Advanced Filtering

```bash
# Combine filters (AND)
journalctl -u nginx.service -p err --since "1 hour ago"

# Show field values
journalctl -F _SYSTEMD_UNIT
journalctl -F PRIORITY

# Custom output
journalctl --output-fields=MESSAGE,PRIORITY,_PID

# Search in messages
journalctl -g "error|fail|warning"
journalctl --grep="connection refused" -i  # case insensitive
```

### journald Configuration

**`/etc/systemd/journald.conf`:**

```ini
[Journal]
# Storage options: volatile, persistent, auto, none
Storage=persistent

# Compress logs
Compress=yes

# Sealing (tamper detection)
Seal=yes

# Rate limiting
RateLimitIntervalSec=30s
RateLimitBurst=10000

# Size limits
SystemMaxUse=4G
SystemKeepFree=1G
SystemMaxFileSize=512M
SystemMaxFiles=100

# Runtime (in-memory) limits
RuntimeMaxUse=256M

# Maximum retention time
MaxRetentionSec=1month
MaxFileSec=1week

# Forward to syslog
ForwardToSyslog=yes
ForwardToKMsg=no
ForwardToConsole=no
ForwardToWall=yes

# Maximum line/field length
LineMax=48K
ReadKMsg=yes
```

### Log Maintenance

```bash
# Check disk usage
journalctl --disk-usage

# Clean old logs (by time)
journalctl --vacuum-time=30d

# Clean old logs (by size)
journalctl --vacuum-size=1G

# Clean old logs (by number of files)
journalctl --vacuum-files=5

# Verify journal integrity
journalctl --verify

# Rotate logs
systemctl kill --signal=SIGUSR2 systemd-journald
```

### Logging from Applications

```bash
# Send message to journal
echo "My message" | systemd-cat -t myapp -p info

# With identifier and priority
systemd-cat -t backup-script -p warning /usr/local/bin/backup.sh

# From code (C)
# sd_journal_print(LOG_INFO, "Hello World");
# sd_journal_send("MESSAGE=Hello World", "PRIORITY=%d", LOG_INFO, NULL);
```

---

## Resource Control with cgroups

systemd uses Linux Control Groups (cgroups) for resource management. This allows fine-grained control over 
CPU, memory, I/O, and more.

### Resource Control Overview

```
┌─────────────────────────────────────────────────────────┐
│                     cgroup Hierarchy                     │
├─────────────────────────────────────────────────────────┤
│  -.slice (root)                                         │
│  ├── system.slice (system services)                     │
│  │   ├── nginx.service                                  │
│  │   ├── mysql.service                                  │
│  │   └── ...                                            │
│  ├── user.slice (user sessions)                         │
│  │   ├── user-1000.slice                                │
│  │   │   └── session-1.scope                            │
│  │   └── ...                                            │
│  └── machine.slice (VMs and containers)                 │
│      ├── container1.scope                               │
│      └── ...                                            │
└─────────────────────────────────────────────────────────┘
```

### CPU Resource Control

```ini
[Service]
# CPU time weight (default 100, range 1-10000)
CPUWeight=50

# Startup CPU weight
StartupCPUWeight=200

# Limit CPU usage (percentage of one CPU)
CPUQuota=80%

# Limit to specific CPUs
AllowedCPUs=0-3
AllowedCPUs=0,2,4

# Allowed NUMA memory nodes
AllowedMemoryNodes=0
```

### Memory Resource Control

```ini
[Service]
# Hard memory limit
MemoryMax=1G

# High memory threshold (triggers reclaim)
MemoryHigh=800M

# Low memory protection
MemoryLow=256M

# Minimum memory protection
MemoryMin=128M

# Swap limit
MemorySwapMax=500M

# Zswap limit
MemoryZSwapMax=200M
```

### I/O Resource Control

```ini
[Service]
# I/O weight (default 100, range 1-10000)
IOWeight=50
StartupIOWeight=200

# I/O limits per device
IOReadBandwidthMax=/dev/sda 100M
IOWriteBandwidthMax=/dev/sda 50M
IOReadIOPSMax=/dev/sda 1000
IOWriteIOPSMax=/dev/sda 500

# Device access
IODeviceWeight=/dev/sda 200
```

### Task Limits

```ini
[Service]
# Maximum number of tasks (threads/processes)
TasksMax=512

# Tasks accounting
TasksAccounting=yes
```

### Other Limits

```ini
[Service]
# Network bandwidth (requires eBPF support)
IPAccounting=yes
IPAddressAllow=192.168.1.0/24
IPAddressDeny=any

# File descriptor limits
LimitNOFILE=65536

# Process limits
LimitNPROC=4096

# Memory lock limit
LimitMEMLOCK=infinity

# Core dump size
LimitCORE=0

# CPU time limit
LimitCPU=3600

# All resource limits (see 'man limits.conf')
LimitAS=infinity         # Address space
LimitFSIZE=infinity      # File size
LimitDATA=infinity       # Data segment
LimitSTACK=8M            # Stack size
LimitRSS=infinity        # Resident set
LimitMSGQUEUE=819200     # POSIX message queues
LimitNICE=0              # Nice priority
LimitRTPRIO=0            # Real-time priority
LimitRTTIME=infinity     # Real-time timeout
LimitSIGPENDING=128222   # Pending signals
LimitLOCKS=infinity      # File locks
```

### Viewing Resource Usage

```bash
# Show resource usage of all units
systemd-cgtop

# Show cgroup tree
systemd-cgls

# Show resource usage for specific unit
systemctl show nginx.service -p MemoryCurrent,CPUUsageNSec

# Detailed status
systemctl status nginx.service

# cgroup info
cat /sys/fs/cgroup/system.slice/nginx.service/memory.current
```

### Runtime Resource Control

```bash
# Set resource limit at runtime
systemctl set-property nginx.service MemoryMax=2G

# Make runtime changes persistent
systemctl set-property nginx.service MemoryMax=2G --runtime

# Reset to default
systemctl revert nginx.service
```

---

## systemd-networkd

systemd-networkd is a system daemon for managing network configurations. It detects and configures network 
devices as they appear.

### Enabling networkd

```bash
# Enable and start networkd
systemctl enable --now systemd-networkd

# Enable and start resolved (for DNS)
systemctl enable --now systemd-resolved

# Link resolv.conf
ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
```

### Configuration File Locations

| Location | Purpose |
|----------|---------|
| `/etc/systemd/network/` | Administrator configuration |
| `/run/systemd/network/` | Runtime configuration |
| `/usr/lib/systemd/network/` | System packages |

Files are processed in alphabetical order. Use numeric prefixes (e.g., `10-eth0.network`).

### Network File Types

| Extension | Purpose |
|-----------|---------|
| `.network` | Network configuration |
| `.netdev` | Virtual network device |
| `.link` | Link configuration |

### Basic Network Configuration

**`/etc/systemd/network/20-wired.network`:**
```ini
[Match]
Name=eth0

[Network]
DHCP=yes
```

**Static IP:**
```ini
[Match]
Name=eth0

[Network]
Address=192.168.1.100/24
Gateway=192.168.1.1
DNS=8.8.8.8
DNS=8.8.4.4
```

### Match Section Options

```ini
[Match]
# Match by name (supports wildcards)
Name=eth*
Name=en*

# Match by MAC address
MACAddress=00:11:22:33:44:55

# Match by device type
Type=ether
Type=wlan

# Match by driver
Driver=e1000

# Match by architecture
Architecture=x86-64

# Match by virtualization
Virtualization=no
Virtualization=container

# Match by path
Path=pci-0000:00:1c.0-*

# Match by host
Host=myserver
```

### Network Section Options

```ini
[Network]
# IP Configuration
DHCP=yes                    # yes, no, ipv4, ipv6
Address=192.168.1.100/24
Gateway=192.168.1.1
DNS=8.8.8.8
NTP=pool.ntp.org
Domains=example.com

# Multiple addresses
Address=192.168.1.100/24
Address=192.168.1.101/24

# IPv6
IPv6AcceptRA=yes
IPv6PrivacyExtensions=yes

# Routing
LLDP=yes
EmitLLDP=yes
LinkLocalAddressing=ipv4
IPv4LLRoute=yes

# Bridge/Bond membership
Bridge=br0
Bond=bond0
VLAN=vlan100
```

### Creating Virtual Devices

**Bridge:**
```ini
# /etc/systemd/network/10-br0.netdev
[NetDev]
Name=br0
Kind=bridge

# /etc/systemd/network/20-br0.network
[Match]
Name=br0

[Network]
Address=192.168.1.1/24
```

**VLAN:**
```ini
# /etc/systemd/network/10-vlan100.netdev
[NetDev]
Name=vlan100
Kind=vlan

[VLAN]
Id=100

# /etc/systemd/network/20-vlan100.network
[Match]
Name=vlan100

[Network]
Address=10.100.0.1/24
```

**Bond:**
```ini
# /etc/systemd/network/10-bond0.netdev
[NetDev]
Name=bond0
Kind=bond

[Bond]
Mode=802.3ad
MIIMonitorSec=100ms
LACPTransmitRate=fast
```

### DHCP Options

```ini
[DHCPv4]
UseDNS=yes
UseNTP=yes
UseHostname=yes
UseDomains=yes
UseRoutes=yes
UseGateway=yes
SendHostname=yes
Hostname=myserver
ClientIdentifier=mac
VendorClassIdentifier=Linux
RouteMetric=100

[DHCPv6]
UseDNS=yes
UseNTP=yes
```

### networkctl Commands

```bash
# Show network status
networkctl status

# Show specific interface
networkctl status eth0

# List all interfaces
networkctl list

# Reconfigure network
networkctl reload
networkctl reconfigure eth0

# Force DHCP renew
networkctl renew eth0

# Take link up/down
networkctl up eth0
networkctl down eth0
```

---

## Boot Process

Understanding the systemd boot process is essential for troubleshooting and optimization.

### Boot Sequence Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    systemd Boot Process                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. BIOS/UEFI → Bootloader (GRUB) → Kernel                     │
│                                                                 │
│  2. Kernel starts systemd (PID 1)                              │
│                                                                 │
│  3. systemd reads:                                              │
│     - /etc/systemd/system/default.target                       │
│     - Configuration files                                       │
│                                                                 │
│  4. Dependency resolution and parallel unit activation:        │
│     ┌──────────────┐                                           │
│     │ local-fs-pre │ → mount critical filesystems              │
│     └──────┬───────┘                                           │
│            │                                                    │
│     ┌──────▼───────┐                                           │
│     │  local-fs    │ → mount local filesystems                 │
│     └──────┬───────┘                                           │
│            │                                                    │
│     ┌──────▼───────┐                                           │
│     │   sysinit    │ → system initialization                   │
│     └──────┬───────┘                                           │
│            │                                                    │
│     ┌──────▼───────┐                                           │
│     │    basic     │ → basic services ready                    │
│     └──────┬───────┘                                           │
│            │                                                    │
│     ┌──────▼───────┐     ┌──────────────┐                     │
│     │ multi-user   │ ──► │  graphical   │                     │
│     └──────────────┘     └──────────────┘                     │
│                                                                 │
│  5. Login prompt / Display Manager                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Analyzing Boot Performance

```bash
# Boot time summary
systemd-analyze

# Boot time by unit
systemd-analyze blame

# Critical chain (slowest path)
systemd-analyze critical-chain

# Critical chain for specific target
systemd-analyze critical-chain graphical.target

# Generate boot chart (SVG)
systemd-analyze plot > boot-chart.svg

# Generate DOT graph
systemd-analyze dot > boot.dot
dot -Tsvg boot.dot > boot.svg

# Verify unit files
systemd-analyze verify myunit.service

# Security analysis
systemd-analyze security
systemd-analyze security nginx.service
```

### Optimizing Boot Time

1. **Identify slow services:**
   ```bash
   systemd-analyze blame | head -20
   ```

2. **Analyze critical path:**
   ```bash
   systemd-analyze critical-chain
   ```

3. **Mask unnecessary services:**
   ```bash
   systemctl mask plymouth-quit-wait.service
   systemctl mask NetworkManager-wait-online.service
   ```

4. **Use socket activation:**
   - Convert services to socket-activated when possible

5. **Set appropriate service type:**
   - Use `Type=notify` for services that support it
   - Avoid `Type=forking` when possible

6. **Reduce dependencies:**
   ```ini
   # Use Wants instead of Requires
   Wants=network.target
   # After doesn't imply dependency
   After=network.target
   ```

### Boot Targets

```bash
# Check default target
systemctl get-default

# Boot to text mode
systemctl set-default multi-user.target

# Boot to graphical mode
systemctl set-default graphical.target

# Boot to emergency mode (kernel parameter)
# Add to kernel command line: systemd.unit=emergency.target

# Boot to rescue mode (kernel parameter)
# Add to kernel command line: systemd.unit=rescue.target
```

### Generator Scripts

Generators create unit files at boot time:

```
/run/systemd/generator.early/    # Before /etc
/run/systemd/generator/          # Between /etc and /usr
/run/systemd/generator.late/     # After /usr
```

```bash
# List generators
/usr/lib/systemd/system-generators/

# Run generators manually
/usr/lib/systemd/system-generators/systemd-fstab-generator /tmp/out /tmp/out /tmp/out
```

---

## Security Features

systemd provides extensive security features for service hardening.

### Filesystem Isolation

```ini
[Service]
# Read-only filesystem
ProtectSystem=strict       # Mount /usr, /boot, /efi, /etc read-only
ProtectSystem=full         # Mount /usr, /boot read-only
ProtectSystem=yes          # Mount /usr read-only

# Protect home directories
ProtectHome=yes            # Make /home, /root, /run/user inaccessible
ProtectHome=read-only      # Make them read-only
ProtectHome=tmpfs          # Mount empty tmpfs

# Protect kernel tunables
ProtectKernelTunables=yes  # Protect /proc/sys, /sys, etc.
ProtectKernelModules=yes   # Prevent module loading
ProtectKernelLogs=yes      # Restrict access to kernel log buffer

# Protect control groups
ProtectControlGroups=yes

# Private /tmp and /var/tmp
PrivateTmp=yes

# Private /dev
PrivateDevices=yes

# Private network namespace
PrivateNetwork=yes

# Private users namespace
PrivateUsers=yes

# Private IPC namespace
PrivateIPC=yes

# Read-only paths
ReadOnlyPaths=/var/lib/myapp

# Inaccessible paths
InaccessiblePaths=/home

# Bind mount paths
BindPaths=/data:/app/data
BindReadOnlyPaths=/etc/ssl:/app/ssl

# Temporary filesystem
TemporaryFileSystem=/var:ro
```

### Capability Restrictions

```ini
[Service]
# Drop all capabilities
CapabilityBoundingSet=

# Allow only specific capabilities
CapabilityBoundingSet=CAP_NET_BIND_SERVICE CAP_CHOWN

# Add ambient capabilities
AmbientCapabilities=CAP_NET_BIND_SERVICE

# No new privileges
NoNewPrivileges=yes
```

### System Call Filtering

```ini
[Service]
# Filter system calls (whitelist)
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources

# System call architectures
SystemCallArchitectures=native

# System call error number
SystemCallErrorNumber=EPERM

# Lock personality (prevent changing execution domain)
LockPersonality=yes
```

### Network Restrictions

```ini
[Service]
# Restrict address families
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6

# IP filtering (requires eBPF)
IPAddressAllow=192.168.1.0/24 localhost
IPAddressDeny=any

# Restrict network interfaces
RestrictNetworkInterfaces=eth0 lo
```

### User and Group Restrictions

```ini
[Service]
# Run as specific user
User=myuser
Group=mygroup

# Dynamic user (ephemeral)
DynamicUser=yes

# Restrict su/sudo
RestrictSUIDSGID=yes

# Supplementary groups
SupplementaryGroups=audio video
```

### Memory and Execution Restrictions

```ini
[Service]
# Restrict realtime scheduling
RestrictRealtime=yes

# Memory deny write execute
MemoryDenyWriteExecute=yes

# Restrict namespace creation
RestrictNamespaces=yes
RestrictNamespaces=~user net

# Protect clock
ProtectClock=yes

# Protect hostname
ProtectHostname=yes
```

### Sandbox Profiles

Example of a highly secured service:

```ini
[Service]
Type=simple
ExecStart=/usr/bin/myservice
User=myservice
Group=myservice

# Filesystem
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ReadWritePaths=/var/lib/myservice

# Capabilities
CapabilityBoundingSet=
NoNewPrivileges=yes

# System calls
SystemCallFilter=@system-service
SystemCallArchitectures=native
SystemCallErrorNumber=EPERM

# Namespaces
PrivateUsers=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
LockPersonality=yes

# Network
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
IPAddressDeny=any
IPAddressAllow=localhost

# Other
RestrictRealtime=yes
RestrictSUIDSGID=yes
MemoryDenyWriteExecute=yes
RemoveIPC=yes
```

### Security Analysis

```bash
# Analyze service security
systemd-analyze security

# Analyze specific service
systemd-analyze security nginx.service

# Output is a security score (0=most secure, 10=least secure)
```

---

## Best Practices

### Unit File Best Practices

1. **Use correct service type:**
   ```ini
   # For services that fork
   Type=forking
   PIDFile=/var/run/myservice.pid

   # For modern services
   Type=notify
   ```

2. **Always define After/Wants properly:**
   ```ini
   [Unit]
   After=network.target
   Wants=network-online.target
   After=network-online.target
   ```

3. **Use proper restart policies:**
   ```ini
   [Service]
   Restart=on-failure
   RestartSec=5s
   StartLimitIntervalSec=300
   StartLimitBurst=5
   ```

4. **Set appropriate timeouts:**
   ```ini
   [Service]
   TimeoutStartSec=30
   TimeoutStopSec=30
   TimeoutAbortSec=30
   ```

5. **Use documentation:**
   ```ini
   [Unit]
   Description=My Service Description
   Documentation=man:myservice(8)
   Documentation=https://myservice.example.com/docs
   ```

### Security Best Practices

1. **Run as non-root user:**
   ```ini
   [Service]
   User=myservice
   Group=myservice
   ```

2. **Use DynamicUser for stateless services:**
   ```ini
   [Service]
   DynamicUser=yes
   StateDirectory=myservice
   ```

3. **Apply sandboxing:**
   ```ini
   [Service]
   ProtectSystem=strict
   ProtectHome=yes
   PrivateTmp=yes
   NoNewPrivileges=yes
   ```

4. **Use capability restrictions:**
   ```ini
   [Service]
   CapabilityBoundingSet=CAP_NET_BIND_SERVICE
   AmbientCapabilities=CAP_NET_BIND_SERVICE
   ```

### Organizational Best Practices

1. **Use drop-in directories for modifications:**
   ```bash
   # Create override
   systemctl edit nginx.service

   # Creates /etc/systemd/system/nginx.service.d/override.conf
   ```

2. **Use template units for multiple instances:**
   ```ini
   # myservice@.service
   [Service]
   ExecStart=/usr/bin/myservice --instance %i
   ```

3. **Group related units:**
   ```ini
   [Unit]
   PartOf=myapp.target
   ```

4. **Use target units to group services:**
   ```ini
   # myapp.target
   [Unit]
   Description=My Application Stack
   Requires=myapp-web.service myapp-worker.service
   After=myapp-web.service myapp-worker.service
   ```

### Logging Best Practices

1. **Use stdout/stderr for logging:**
   ```ini
   [Service]
   StandardOutput=journal
   StandardError=journal
   ```

2. **Add syslog identifier:**
   ```ini
   [Service]
   SyslogIdentifier=myservice
   SyslogFacility=daemon
   SyslogLevel=info
   ```

3. **Consider log levels:**
   ```ini
   [Service]
   LogLevelMax=notice
   ```

---

## Troubleshooting

### Common Issues and Solutions

#### Service Won't Start

```bash
# Check status
systemctl status myservice.service

# View detailed logs
journalctl -u myservice.service -xe

# Check unit file syntax
systemd-analyze verify myservice.service

# Check if masked
systemctl is-enabled myservice.service
# If "masked", unmask it
systemctl unmask myservice.service
```

#### Service Keeps Restarting

```bash
# Check restart limits
systemctl show myservice.service -p StartLimitBurst,StartLimitIntervalSec

# View restart history
journalctl -u myservice.service --since "1 hour ago"

# Reset failed state
systemctl reset-failed myservice.service
```

#### Dependency Issues

```bash
# List dependencies
systemctl list-dependencies myservice.service

# Check if dependency failed
systemctl list-units --failed

# Check ordering
systemd-analyze critical-chain myservice.service

# Verify dependencies exist
systemd-analyze verify myservice.service
```

#### Boot Problems

```bash
# Emergency mode (kernel parameter)
systemd.unit=emergency.target

# Rescue mode (kernel parameter)
systemd.unit=rescue.target

# Debug shell (kernel parameter)
systemd.debug-shell=1

# From recovery, view logs
journalctl -xb

# Check default target
systemctl get-default
```

### Debug Mode

```bash
# Enable debug logging
systemctl set-log-level debug
systemctl daemon-reload

# Check systemd manager status
systemctl status

# View manager logs
journalctl -b _PID=1

# Reset log level
systemctl set-log-level info
```

### Useful Diagnostic Commands

```bash
# System status overview
systemctl status

# Failed units
systemctl --failed

# Show unit properties
systemctl show nginx.service

# Unit file location
systemctl show nginx.service -p FragmentPath

# List all loaded units
systemctl list-units --all

# Check configuration
systemd-analyze verify /etc/systemd/system/myservice.service

# Dump all unit files
systemctl dump

# Show manager configuration
systemctl show-environment
```

### Recovering from Bad Unit Files

```bash
# If system won't boot due to bad unit file:
# 1. Boot with rescue target
#    Add to kernel cmdline: systemd.unit=rescue.target

# 2. Edit/remove the problematic file
nano /etc/systemd/system/bad-unit.service

# 3. Reload daemon
systemctl daemon-reload

# 4. Continue boot
systemctl default
```

### Log Analysis

```bash
# Show errors only
journalctl -p err -b

# Show by time
journalctl -b --since "10 minutes ago"

# Show specific boot
journalctl -b -1 -p err

# Correlate events
journalctl -b --no-pager | grep -E "(start|stop|fail)"

# Export logs for analysis
journalctl -b -o json > logs.json
```

---

## Advanced Topics

### Template Units

Template units allow creating multiple instances from a single unit file.

**`myservice@.service`:**
```ini
[Unit]
Description=My Service Instance %i

[Service]
ExecStart=/usr/bin/myservice --instance %i
User=%i

[Install]
WantedBy=multi-user.target
```

```bash
# Enable instances
systemctl enable myservice@worker1.service
systemctl enable myservice@worker2.service

# Start instances
systemctl start myservice@worker1.service
systemctl start myservice@worker2.service
```

**Template Specifiers:**

| Specifier | Description |
|-----------|-------------|
| `%i` | Instance name (unescaped) |
| `%I` | Instance name (escaped) |
| `%n` | Full unit name |
| `%N` | Full unit name (unescaped) |
| `%p` | Unit prefix (before @) |
| `%u` | User name running systemd |
| `%U` | User UID |
| `%h` | User home directory |
| `%s` | User shell |
| `%m` | Machine ID |
| `%b` | Boot ID |
| `%H` | Host name |
| `%t` | Runtime directory (/run or $XDG_RUNTIME_DIR) |
| `%S` | State directory (/var/lib or $XDG_CONFIG_HOME) |
| `%C` | Cache directory (/var/cache or $XDG_CACHE_HOME) |
| `%L` | Log directory (/var/log) |
| `%%` | Literal % |

### Drop-in Directories

Modify units without editing the original file:

```bash
# Create drop-in
mkdir -p /etc/systemd/system/nginx.service.d/
cat > /etc/systemd/system/nginx.service.d/override.conf << EOF
[Service]
MemoryMax=2G
CPUQuota=50%
EOF

# Or use systemctl edit
systemctl edit nginx.service

# Reload
systemctl daemon-reload
systemctl restart nginx.service

# View effective configuration
systemctl cat nginx.service
```

### User Services

systemd can manage per-user services:

```bash
# User service location
~/.config/systemd/user/

# Manage user services
systemctl --user start myservice.service
systemctl --user enable myservice.service
systemctl --user status myservice.service

# Enable user services at boot (without login)
loginctl enable-linger username

# User journal
journalctl --user -u myservice.service
```

**Example user service:**
```ini
# ~/.config/systemd/user/myapp.service
[Unit]
Description=My User Application

[Service]
ExecStart=/home/user/bin/myapp
Restart=on-failure

[Install]
WantedBy=default.target
```

### Transient Units

Create units at runtime without files:

```bash
# Run a transient service
systemd-run --unit=my-temp-job /usr/bin/my-script.sh

# With options
systemd-run --unit=my-temp-job \
--property=CPUQuota=50% \
--property=MemoryMax=1G \
/usr/bin/my-script.sh

# Run as scope (not service)
systemd-run --scope /usr/bin/my-script.sh

# Timer-based transient
systemd-run --on-calendar="*:0/5" /usr/bin/my-script.sh

# View transient units
systemctl list-units --type=service | grep run-

# Clean up
systemctl stop my-temp-job.service
```

### Path Units

Trigger services based on file system changes:

```ini
# /etc/systemd/system/watch-config.path
[Unit]
Description=Watch for config changes

[Path]
PathModified=/etc/myapp/config.yaml
PathChanged=/etc/myapp/
PathExists=/var/run/trigger
PathExistsGlob=/var/spool/jobs/*

# Debounce (make sure changes have stopped)
MakeDirectory=yes
DirectoryMode=0755

[Install]
WantedBy=multi-user.target
```

### Portable Services

Package services as portable, self-contained images:

```bash
# Create portable service image
mkdir -p myservice/usr/lib/systemd/system
# Add service files and root filesystem

# Attach image
portablectl attach myservice.raw

# List attached
portablectl list

# Enable and start
systemctl enable --now myservice.service

# Detach
portablectl detach myservice.raw
```

### Systemd-nspawn Containers

Light-weight containers using systemd-nspawn:

```bash
# Create container from debootstrap
debootstrap stable /var/lib/machines/mycontainer

# Boot container
systemd-nspawn -D /var/lib/machines/mycontainer -b

# Or use machinectl
machinectl start mycontainer
machinectl login mycontainer

# List containers
machinectl list

# Container settings
/etc/systemd/nspawn/mycontainer.nspawn
```

### Credentials

Securely pass secrets to services:

```ini
[Service]
# Load credentials
LoadCredential=password:/etc/secrets/myservice-password
LoadCredentialEncrypted=api-key:/etc/secrets/api-key.encrypted

# Access in service as /run/credentials/myservice.service/password
```

```bash
# Encrypt credentials
systemd-creds encrypt - /etc/secrets/api-key.encrypted < /tmp/api-key

# Service can read from
# /run/credentials/myservice.service/api-key
```

### Extension Images

Extend system with overlay images:

```bash
# List extensions
systemd-sysext list

# Add extension
systemd-sysext merge

# Remove extensions
systemd-sysext unmerge

# Refresh
systemd-sysext refresh
```

---

## Quick Reference

### Essential Commands Cheat Sheet

```bash
# Service Management
systemctl start|stop|restart|reload <unit>
systemctl enable|disable <unit>
systemctl status <unit>
systemctl mask|unmask <unit>

# System State
systemctl poweroff|reboot|suspend|hibernate
systemctl get-default
systemctl set-default <target>
systemctl isolate <target>

# Information
systemctl list-units [--type=<type>] [--state=<state>]
systemctl list-unit-files
systemctl list-dependencies <unit>
systemctl cat <unit>
systemctl show <unit>

# Configuration
systemctl edit <unit>
systemctl daemon-reload
systemctl daemon-reexec

# Logging
journalctl -u <unit>
journalctl -f
journalctl -b
journalctl --since "1 hour ago"
journalctl -p err

# Analysis
systemd-analyze
systemd-analyze blame
systemd-analyze critical-chain
systemd-analyze security

# Network
networkctl list
networkctl status

# Resource Control
systemd-cgtop
systemd-cgls
```

### Unit File Template

```ini
[Unit]
Description=My Service
Documentation=https://example.com
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=myuser
Group=mygroup
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/myapp
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

# Security
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp

[Install]
WantedBy=multi-user.target
```

---

## Additional Resources

### Official Documentation

- [systemd Official Documentation](https://www.freedesktop.org/wiki/Software/systemd/)
- [systemd Man Pages](https://www.freedesktop.org/software/systemd/man/)
- [systemd GitHub Repository](https://github.com/systemd/systemd)

### Man Pages Reference

```bash
# Core
man systemd
man systemctl
man journalctl

# Unit files
man systemd.unit
man systemd.service
man systemd.socket
man systemd.timer
man systemd.path
man systemd.mount

# Configuration
man systemd.exec
man systemd.resource-control
man systemd.directives

# Tools
man systemd-analyze
man systemd-run
man loginctl
man networkctl
man hostnamectl
man timedatectl
man localectl
```

### Common Configuration Files

| File | Purpose |
|------|---------|
| `/etc/systemd/system.conf` | systemd manager configuration |
| `/etc/systemd/user.conf` | User manager configuration |
| `/etc/systemd/journald.conf` | Journal configuration |
| `/etc/systemd/logind.conf` | Login manager configuration |
| `/etc/systemd/networkd.conf` | Network daemon configuration |
| `/etc/systemd/resolved.conf` | DNS resolver configuration |
| `/etc/systemd/timesyncd.conf` | Time sync configuration |

---

*This guide covers systemd version 250+. Some features may not be available in older versions.*

