# Disk Partitioning Schemes: LUKS Encryption, LVM & Btrfs

> A comprehensive guide to advanced disk partitioning for Arch Linux / Omarchy installations.

---

## Table of Contents

1. [Overview & Concepts](#overview--concepts)
2. [Partition Table Types (GPT vs MBR)](#partition-table-types-gpt-vs-mbr)
3. [Basic Partitioning with fdisk/gdisk](#basic-partitioning-with-fdiskgdisk)
4. [LUKS Encryption](#luks-encryption)
5. [LVM (Logical Volume Manager)](#lvm-logical-volume-manager)
6. [Btrfs File System](#btrfs-file-system)
7. [Combined Setups](#combined-setups)
8. [Boot Configuration for Each Setup](#boot-configuration-for-each-setup)
9. [Maintenance & Recovery](#maintenance--recovery)

---

## Overview & Concepts

### Why Use Advanced Partitioning?

| Technology | Purpose | Benefits |
|------------|---------|----------|
| **LUKS** | Full disk encryption | Data security, protection at rest |
| **LVM** | Logical volume management | Flexible resizing, snapshots, multiple volumes |
| **Btrfs** | Modern copy-on-write filesystem | Snapshots, compression, subvolumes, checksums |

### Common Partition Layouts

```
┌─────────────────────────────────────────────────────────────┐
│ Simple (No Encryption)                                       │
├─────────────────────────────────────────────────────────────┤
│ EFI (512M-1G) │ Swap (4-16G) │ Root (/) ext4/btrfs          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ LUKS Encrypted Root                                          │
├─────────────────────────────────────────────────────────────┤
│ EFI (1G) │ LUKS Container → ext4/btrfs root + swap file     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ LVM on LUKS (Most Flexible + Secure)                        │
├─────────────────────────────────────────────────────────────┤
│ EFI (1G) │ LUKS → LVM PV → VG → LV-root, LV-home, LV-swap   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Btrfs with Subvolumes                                        │
├─────────────────────────────────────────────────────────────┤
│ EFI (1G) │ Swap │ Btrfs → @, @home, @snapshots, @var        │
└─────────────────────────────────────────────────────────────┘
```

---

## Partition Table Types (GPT vs MBR)

### GPT (GUID Partition Table) - Recommended
```bash
# For UEFI systems (modern hardware)
# Supports disks > 2TB
# Up to 128 partitions
# Required for UEFI boot

# Create GPT table
fdisk /dev/nvme0n1
# Press 'g' to create new GPT table
```

### MBR (Master Boot Record) - Legacy
```bash
# For BIOS/Legacy systems
# Limited to 2TB disks
# Maximum 4 primary partitions (or 3 primary + 1 extended)

# Create MBR table
fdisk /dev/sda
# Press 'o' to create new DOS/MBR table
```

### Check Current Partition Table
```bash
fdisk -l /dev/nvme0n1
# or
parted /dev/nvme0n1 print
# or
blkid -o value -s PTTYPE /dev/nvme0n1
```

---

## Basic Partitioning with fdisk/gdisk

### Using fdisk (Interactive)
```bash
fdisk /dev/nvme0n1

# Commands:
# g     - create new GPT partition table
# n     - new partition
# d     - delete partition
# t     - change partition type
# p     - print partition table
# w     - write changes and exit
# q     - quit without saving
```

### Using gdisk (GPT-specific)
```bash
gdisk /dev/nvme0n1

# Commands similar to fdisk
# o     - create new GPT table
# x     - expert mode (for advanced options)
```

### Using parted (Scriptable)
```bash
# Create GPT table
parted /dev/nvme0n1 mklabel gpt

# Create EFI partition (1GB)
parted /dev/nvme0n1 mkpart "EFI" fat32 1MiB 1GiB
parted /dev/nvme0n1 set 1 esp on

# Create root partition (rest of disk)
parted /dev/nvme0n1 mkpart "Root" ext4 1GiB 100%

# View results
parted /dev/nvme0n1 print
```

### Partition Type Codes (GPT)

| Type Code | Description |
|-----------|-------------|
| `ef00` | EFI System Partition |
| `8200` | Linux swap |
| `8300` | Linux filesystem |
| `8301` | Linux reserved |
| `8302` | Linux /home |
| `8303` | Linux x86-64 root (/) |
| `8304` | Linux x86-64 /usr |
| `8e00` | Linux LVM |

---

## LUKS Encryption

### What is LUKS?
**Linux Unified Key Setup** - The standard for Linux disk encryption. Provides:
- Strong AES encryption (default: aes-xts-plain64)
- Multiple key slots (up to 8 passphrases/keyfiles)
- Header with metadata

### LUKS1 vs LUKS2
| Feature | LUKS1 | LUKS2 |
|---------|-------|-------|
| Default cipher | aes-xts-plain64 | aes-xts-plain64 |
| Key derivation | PBKDF2 | Argon2id (memory-hard) |
| Header size | 2 MiB | 16 MiB |
| GRUB support | Full | Limited (no Argon2id) |
| Recommended | Legacy/GRUB | systemd-boot |

### Create LUKS Encrypted Partition

#### Step 1: Partition the Disk
```bash
fdisk /dev/nvme0n1
# Create:
# - /dev/nvme0n1p1: 1G EFI partition (type ef00)
# - /dev/nvme0n1p2: Rest of disk for LUKS (type 8309 or 8300)
```

#### Step 2: Create LUKS Container
```bash
# LUKS2 (recommended for systemd-boot)
cryptsetup luksFormat /dev/nvme0n1p2

# LUKS1 (required for GRUB with encryption)
cryptsetup luksFormat --type luks1 /dev/nvme0n1p2

# With specific options
cryptsetup luksFormat --type luks2 \
    --cipher aes-xts-plain64 \
    --key-size 512 \
    --hash sha512 \
    --iter-time 5000 \
    /dev/nvme0n1p2
```

#### Step 3: Open LUKS Container
```bash
# Open and map to /dev/mapper/cryptroot
cryptsetup open /dev/nvme0n1p2 cryptroot

# Verify
ls /dev/mapper/
# Should show: cryptroot
```

#### Step 4: Create Filesystem Inside LUKS
```bash
# ext4
mkfs.ext4 /dev/mapper/cryptroot

# Or Btrfs
mkfs.btrfs /dev/mapper/cryptroot
```

#### Step 5: Mount and Install
```bash
mount /dev/mapper/cryptroot /mnt
mount --mkdir /dev/nvme0n1p1 /mnt/boot
```

### LUKS Key Management

```bash
# View key slots
cryptsetup luksDump /dev/nvme0n1p2

# Add additional passphrase (up to 8 slots)
cryptsetup luksAddKey /dev/nvme0n1p2

# Add keyfile
dd if=/dev/urandom of=/root/keyfile bs=4096 count=1
chmod 400 /root/keyfile
cryptsetup luksAddKey /dev/nvme0n1p2 /root/keyfile

# Remove a key slot
cryptsetup luksRemoveKey /dev/nvme0n1p2

# Kill specific slot
cryptsetup luksKillSlot /dev/nvme0n1p2 1
```

### LUKS Header Backup (CRITICAL!)
```bash
# Backup header (store securely offline!)
cryptsetup luksHeaderBackup /dev/nvme0n1p2 --header-backup-file luks-header-backup.img

# Restore header
cryptsetup luksHeaderRestore /dev/nvme0n1p2 --header-backup-file luks-header-backup.img
```

---

## LVM (Logical Volume Manager)

### LVM Concepts

```
┌─────────────────────────────────────────────────────────────┐
│                    LVM Architecture                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Physical Volumes (PV)    →    Volume Groups (VG)            │
│  /dev/sda2, /dev/sdb1          Combined storage pool        │
│                                      │                       │
│                                      ▼                       │
│                             Logical Volumes (LV)             │
│                             lv-root, lv-home, lv-swap        │
│                                      │                       │
│                                      ▼                       │
│                              File Systems                    │
│                             ext4, btrfs, swap                │
└─────────────────────────────────────────────────────────────┘
```

### LVM Terminology

| Term | Description |
|------|-------------|
| **PV** (Physical Volume) | Physical partition or disk initialized for LVM |
| **VG** (Volume Group) | Pool of storage from one or more PVs |
| **LV** (Logical Volume) | Virtual partition carved from a VG |
| **PE** (Physical Extent) | Smallest allocatable unit (default 4 MiB) |

### Install LVM Tools
```bash
pacman -S lvm2
```

### Create LVM Setup

#### Step 1: Create Physical Volume
```bash
# Initialize partition for LVM
pvcreate /dev/nvme0n1p2

# Verify
pvs
pvdisplay
```

#### Step 2: Create Volume Group
```bash
# Create VG named "vg0"
vgcreate vg0 /dev/nvme0n1p2

# Verify
vgs
vgdisplay
```

#### Step 3: Create Logical Volumes
```bash
# Create swap (8GB)
lvcreate -L 8G vg0 -n lv-swap

# Create root (50GB)
lvcreate -L 50G vg0 -n lv-root

# Create home (use remaining space)
lvcreate -l 100%FREE vg0 -n lv-home

# Verify
lvs
lvdisplay
```

#### Step 4: Format Logical Volumes
```bash
mkswap /dev/vg0/lv-swap
mkfs.ext4 /dev/vg0/lv-root
mkfs.ext4 /dev/vg0/lv-home
```

#### Step 5: Mount
```bash
mount /dev/vg0/lv-root /mnt
mount --mkdir /dev/vg0/lv-home /mnt/home
mount --mkdir /dev/nvme0n1p1 /mnt/boot
swapon /dev/vg0/lv-swap
```

### LVM Operations

```bash
# Extend logical volume
lvextend -L +10G /dev/vg0/lv-home
# Then resize filesystem
resize2fs /dev/vg0/lv-home  # ext4
btrfs filesystem resize max /home  # btrfs

# Reduce logical volume (DANGER - backup first!)
umount /home
e2fsck -f /dev/vg0/lv-home
resize2fs /dev/vg0/lv-home 40G
lvreduce -L 40G /dev/vg0/lv-home

# Add new disk to volume group
pvcreate /dev/sdb1
vgextend vg0 /dev/sdb1

# Remove physical volume from VG
pvmove /dev/sda2  # Move data off first
vgreduce vg0 /dev/sda2

# Create LVM snapshot
lvcreate -L 5G -s -n root-snapshot /dev/vg0/lv-root
```

---

## Btrfs File System

### Btrfs Features

| Feature | Description |
|---------|-------------|
| **Copy-on-Write (CoW)** | Data never overwritten in place |
| **Subvolumes** | Logical divisions, mountable separately |
| **Snapshots** | Instant, space-efficient copies |
| **Compression** | Transparent zstd/lzo/zlib compression |
| **Checksums** | Data integrity verification |
| **RAID** | Built-in RAID 0, 1, 10, 5, 6 |

### Create Btrfs Filesystem
```bash
# Simple creation
mkfs.btrfs /dev/nvme0n1p3

# With label
mkfs.btrfs -L "ArchRoot" /dev/nvme0n1p3

# Force (destroy existing data)
mkfs.btrfs -f /dev/nvme0n1p3
```

### Btrfs Subvolume Layout (Recommended)

```
btrfs root
├── @            → mounted as /
├── @home        → mounted as /home
├── @snapshots   → mounted as /.snapshots
├── @var_log     → mounted as /var/log
├── @var_cache   → mounted as /var/cache (optional, exclude from snapshots)
└── @swap        → for swap file (CoW disabled)
```

### Create Subvolumes
```bash
# Mount the Btrfs partition
mount /dev/nvme0n1p3 /mnt

# Create subvolumes
btrfs subvolume create /mnt/@
btrfs subvolume create /mnt/@home
btrfs subvolume create /mnt/@snapshots
btrfs subvolume create /mnt/@var_log
btrfs subvolume create /mnt/@var_cache
btrfs subvolume create /mnt/@swap

# List subvolumes
btrfs subvolume list /mnt

# Unmount
umount /mnt
```

### Mount Subvolumes with Options
```bash
# Recommended mount options
OPTS="compress=zstd:1,noatime,space_cache=v2,ssd"

# Mount root subvolume
mount -o subvol=@,$OPTS /dev/nvme0n1p3 /mnt

# Create mount points
mkdir -p /mnt/{home,.snapshots,var/log,var/cache,swap,boot}

# Mount other subvolumes
mount -o subvol=@home,$OPTS /dev/nvme0n1p3 /mnt/home
mount -o subvol=@snapshots,$OPTS /dev/nvme0n1p3 /mnt/.snapshots
mount -o subvol=@var_log,$OPTS /dev/nvme0n1p3 /mnt/var/log
mount -o subvol=@var_cache,$OPTS /dev/nvme0n1p3 /mnt/var/cache
mount -o subvol=@swap,noatime /dev/nvme0n1p3 /mnt/swap

# Mount EFI
mount /dev/nvme0n1p1 /mnt/boot
```

### Btrfs Mount Options Explained

| Option | Description |
|--------|-------------|
| `compress=zstd:1` | Zstandard compression level 1 (fast) |
| `noatime` | Don't update access times (better performance) |
| `space_cache=v2` | Improved free space tracking |
| `ssd` | Optimizations for SSDs |
| `discard=async` | Async TRIM for SSDs |
| `autodefrag` | Auto defragmentation (good for databases/VMs) |

### Btrfs Snapshots

```bash
# Create read-only snapshot
btrfs subvolume snapshot -r /mnt/@ /mnt/@snapshots/root-$(date +%Y%m%d)

# Create writable snapshot
btrfs subvolume snapshot /mnt/@ /mnt/@snapshots/root-writable

# List snapshots
btrfs subvolume list -s /mnt

# Delete snapshot
btrfs subvolume delete /mnt/@snapshots/root-20240101

# Restore from snapshot (boot from live USB)
mount /dev/nvme0n1p3 /mnt
mv /mnt/@ /mnt/@.broken
btrfs subvolume snapshot /mnt/@snapshots/root-good /mnt/@
```

### Swap File on Btrfs
```bash
# Create swap file (disable CoW!)
btrfs filesystem mkswapfile --size 8G /swap/swapfile

# Or manually
truncate -s 0 /swap/swapfile
chattr +C /swap/swapfile  # Disable CoW
fallocate -l 8G /swap/swapfile
chmod 600 /swap/swapfile
mkswap /swap/swapfile
swapon /swap/swapfile

# Add to fstab
echo "/swap/swapfile none swap defaults 0 0" >> /etc/fstab
```

### Btrfs Maintenance
```bash
# Check filesystem
btrfs check /dev/nvme0n1p3

# Scrub (verify checksums)
btrfs scrub start /
btrfs scrub status /

# Balance (redistribute data)
btrfs balance start /
btrfs balance status /

# Show filesystem info
btrfs filesystem show
btrfs filesystem df /
btrfs filesystem usage /

# Defragment
btrfs filesystem defragment -r /
```

---

## Combined Setups

### Setup 1: LUKS + ext4 (Simple Encrypted)

```bash
# Partition layout:
# /dev/nvme0n1p1 - 1G EFI
# /dev/nvme0n1p2 - Rest LUKS

# Create LUKS
cryptsetup luksFormat /dev/nvme0n1p2
cryptsetup open /dev/nvme0n1p2 cryptroot

# Create filesystems
mkfs.fat -F32 /dev/nvme0n1p1
mkfs.ext4 /dev/mapper/cryptroot

# Mount
mount /dev/mapper/cryptroot /mnt
mount --mkdir /dev/nvme0n1p1 /mnt/boot

# Create swap file
dd if=/dev/zero of=/mnt/swapfile bs=1M count=8192
chmod 600 /mnt/swapfile
mkswap /mnt/swapfile
```

### Setup 2: LUKS + LVM (Flexible Encrypted)

```bash
# Partition layout:
# /dev/nvme0n1p1 - 1G EFI
# /dev/nvme0n1p2 - Rest LUKS

# Create LUKS
cryptsetup luksFormat /dev/nvme0n1p2
cryptsetup open /dev/nvme0n1p2 cryptlvm

# Create LVM inside LUKS
pvcreate /dev/mapper/cryptlvm
vgcreate vg0 /dev/mapper/cryptlvm
lvcreate -L 8G vg0 -n swap
lvcreate -L 50G vg0 -n root
lvcreate -l 100%FREE vg0 -n home

# Create filesystems
mkfs.fat -F32 /dev/nvme0n1p1
mkswap /dev/vg0/swap
mkfs.ext4 /dev/vg0/root
mkfs.ext4 /dev/vg0/home

# Mount
mount /dev/vg0/root /mnt
mount --mkdir /dev/vg0/home /mnt/home
mount --mkdir /dev/nvme0n1p1 /mnt/boot
swapon /dev/vg0/swap
```

### Setup 3: LUKS + Btrfs Subvolumes (Modern Encrypted)

```bash
# Partition layout:
# /dev/nvme0n1p1 - 1G EFI
# /dev/nvme0n1p2 - Rest LUKS

# Create LUKS
cryptsetup luksFormat /dev/nvme0n1p2
cryptsetup open /dev/nvme0n1p2 cryptroot

# Create Btrfs
mkfs.btrfs /dev/mapper/cryptroot

# Create subvolumes
mount /dev/mapper/cryptroot /mnt
btrfs subvolume create /mnt/@
btrfs subvolume create /mnt/@home
btrfs subvolume create /mnt/@snapshots
btrfs subvolume create /mnt/@swap
umount /mnt

# Mount with options
OPTS="compress=zstd:1,noatime,space_cache=v2"
mount -o subvol=@,$OPTS /dev/mapper/cryptroot /mnt
mkdir -p /mnt/{home,.snapshots,swap,boot}
mount -o subvol=@home,$OPTS /dev/mapper/cryptroot /mnt/home
mount -o subvol=@snapshots,$OPTS /dev/mapper/cryptroot /mnt/.snapshots
mount -o subvol=@swap,noatime /dev/mapper/cryptroot /mnt/swap
mount /dev/nvme0n1p1 /mnt/boot

# Create swap file
btrfs filesystem mkswapfile --size 8G /mnt/swap/swapfile
swapon /mnt/swap/swapfile
```

---

## Boot Configuration for Each Setup

### Unencrypted Systems

#### GRUB
```bash
pacman -S grub efibootmgr
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
```

#### systemd-boot
```bash
bootctl install

cat > /boot/loader/entries/arch.conf << EOF
title   Arch Linux
linux   /vmlinuz-linux
initrd  /amd-ucode.img
initrd  /initramfs-linux.img
options root=UUID=$(blkid -s UUID -o value /dev/nvme0n1p3) rw
EOF
```

### LUKS Encrypted (No LVM)

#### mkinitcpio.conf
```bash
# Edit /etc/mkinitcpio.conf
# Add 'encrypt' hook BEFORE 'filesystems':
HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block encrypt filesystems fsck)

# Regenerate
mkinitcpio -P
```

#### GRUB with LUKS
```bash
# Edit /etc/default/grub
GRUB_CMDLINE_LINUX="cryptdevice=UUID=<LUKS-UUID>:cryptroot root=/dev/mapper/cryptroot"

# For LUKS2 with GRUB (requires PBKDF2):
GRUB_ENABLE_CRYPTODISK=y

grub-mkconfig -o /boot/grub/grub.cfg
```

#### systemd-boot with LUKS
```bash
cat > /boot/loader/entries/arch.conf << EOF
title   Arch Linux (Encrypted)
linux   /vmlinuz-linux
initrd  /amd-ucode.img
initrd  /initramfs-linux.img
options cryptdevice=UUID=<LUKS-UUID>:cryptroot root=/dev/mapper/cryptroot rw
EOF
```

### LUKS + LVM

#### mkinitcpio.conf
```bash
# Add both 'encrypt' and 'lvm2' hooks:
HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block encrypt lvm2 filesystems fsck)

# Regenerate
mkinitcpio -P
```

#### GRUB with LUKS+LVM
```bash
# Edit /etc/default/grub
GRUB_CMDLINE_LINUX="cryptdevice=UUID=<LUKS-UUID>:cryptlvm root=/dev/vg0/root"

grub-mkconfig -o /boot/grub/grub.cfg
```

#### systemd-boot with LUKS+LVM
```bash
cat > /boot/loader/entries/arch.conf << EOF
title   Arch Linux (Encrypted LVM)
linux   /vmlinuz-linux
initrd  /amd-ucode.img
initrd  /initramfs-linux.img
options cryptdevice=UUID=<LUKS-UUID>:cryptlvm root=/dev/vg0/root rw
EOF
```

### Btrfs Specific Options

```bash
# Add rootflags for Btrfs subvolume
options cryptdevice=UUID=<LUKS-UUID>:cryptroot root=/dev/mapper/cryptroot rootflags=subvol=@ rw

# Or for GRUB
GRUB_CMDLINE_LINUX="cryptdevice=UUID=<LUKS-UUID>:cryptroot root=/dev/mapper/cryptroot rootflags=subvol=@"
```

### Get UUIDs for Configuration
```bash
# Get UUID of LUKS partition (not the mapped device!)
blkid /dev/nvme0n1p2

# Get UUID of root filesystem
blkid /dev/mapper/cryptroot
# Or for LVM
blkid /dev/vg0/root
```

---

## Maintenance & Recovery

### Rescue Mode from Live USB

#### Mount Encrypted System
```bash
# Open LUKS
cryptsetup open /dev/nvme0n1p2 cryptroot

# For LVM on LUKS
vgchange -ay  # Activate volume groups

# Mount
mount /dev/mapper/cryptroot /mnt  # Or /dev/vg0/root for LVM
mount /dev/nvme0n1p1 /mnt/boot

# Chroot
arch-chroot /mnt
```

#### Mount Btrfs with Subvolumes
```bash
cryptsetup open /dev/nvme0n1p2 cryptroot
mount -o subvol=@ /dev/mapper/cryptroot /mnt
mount -o subvol=@home /dev/mapper/cryptroot /mnt/home
mount /dev/nvme0n1p1 /mnt/boot
arch-chroot /mnt
```

### Fix Common Boot Issues

#### Regenerate Initramfs
```bash
arch-chroot /mnt
mkinitcpio -P
```

#### Reinstall Bootloader
```bash
# GRUB
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg

# systemd-boot
bootctl install
```

#### Fix fstab
```bash
# Regenerate fstab
genfstab -U /mnt >> /mnt/etc/fstab.new
# Review and replace if correct
```

### Resize Operations

#### Resize LUKS Container
```bash
# Shrink (DANGEROUS - backup first!)
# 1. Shrink filesystem inside LUKS
# 2. Shrink LUKS container
cryptsetup resize cryptroot --size <new-size-in-sectors>
# 3. Shrink underlying partition

# Grow (safe)
# 1. Grow underlying partition
# 2. Grow LUKS container
cryptsetup resize cryptroot
# 3. Grow filesystem
resize2fs /dev/mapper/cryptroot  # ext4
btrfs filesystem resize max /    # btrfs
```

#### Resize LVM
```bash
# Extend LV
lvextend -L +20G /dev/vg0/root
resize2fs /dev/vg0/root

# Reduce LV (backup first!)
umount /
e2fsck -f /dev/vg0/root
resize2fs /dev/vg0/root 30G
lvreduce -L 30G /dev/vg0/root
```

### Backup Strategies

```bash
# LUKS Header Backup (CRITICAL!)
cryptsetup luksHeaderBackup /dev/nvme0n1p2 --header-backup-file /backup/luks-header.img

# Btrfs Snapshot for System Backup
btrfs subvolume snapshot -r / /.snapshots/$(date +%Y%m%d-%H%M%S)

# Send Btrfs snapshot to external drive
btrfs send /.snapshots/backup-snap | btrfs receive /mnt/external-btrfs/

# LVM Snapshot for Backup
lvcreate -L 10G -s -n backup-snap /dev/vg0/root
dd if=/dev/vg0/backup-snap | gzip > /backup/root-backup.img.gz
lvremove /dev/vg0/backup-snap
```

---

## Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| List block devices | `lsblk -f` |
| Show partition UUIDs | `blkid` |
| Open LUKS | `cryptsetup open /dev/sdX cryptname` |
| Close LUKS | `cryptsetup close cryptname` |
| LUKS status | `cryptsetup status cryptname` |
| List PVs | `pvs` or `pvdisplay` |
| List VGs | `vgs` or `vgdisplay` |
| List LVs | `lvs` or `lvdisplay` |
| Activate VGs | `vgchange -ay` |
| Btrfs subvolume list | `btrfs subvolume list /` |
| Btrfs filesystem info | `btrfs filesystem show` |

### Partition Type Quick Reference

| Use Case | Partition Type | Code |
|----------|----------------|------|
| EFI System | EFI System Partition | `ef00` |
| Linux Root | Linux filesystem | `8300` |
| Linux Swap | Linux swap | `8200` |
| LVM | Linux LVM | `8e00` |
| LUKS | Linux LUKS | `8309` |

---

## Additional Resources

- [Arch Wiki - dm-crypt](https://wiki.archlinux.org/title/Dm-crypt)
- [Arch Wiki - LVM](https://wiki.archlinux.org/title/LVM)
- [Arch Wiki - Btrfs](https://wiki.archlinux.org/title/Btrfs)
- [Arch Wiki - Partitioning](https://wiki.archlinux.org/title/Partitioning)
- [Arch Wiki - GRUB](https://wiki.archlinux.org/title/GRUB)
- [Arch Wiki - systemd-boot](https://wiki.archlinux.org/title/Systemd-boot)

---

*Last updated: March 2026*
