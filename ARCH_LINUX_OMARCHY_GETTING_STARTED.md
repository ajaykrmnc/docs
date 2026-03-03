# Arch Linux Omarchy - Getting Started Guide

> Omarchy is a beautiful, modern & opinionated Linux distribution by DHH, built on top of Arch Linux.
> Official website: [omarchy.org](https://omarchy.org) | GitHub: [basecamp/omarchy](https://github.com/basecamp/omarchy)

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Installation Requirements](#pre-installation-requirements)
3. [Booting the Installation Medium](#booting-the-installation-medium)
4. [Disk Partitioning](#disk-partitioning)
5. [Formatting Partitions](#formatting-partitions)
6. [Mounting the File Systems](#mounting-the-file-systems)
7. [Base System Installation](#base-system-installation)
8. [Initramfs Configuration](#initramfs-configuration)
9. [Boot Loader Setup](#boot-loader-setup)
10. [Installing Omarchy](#installing-omarchy)
11. [Post-Installation](#post-installation)
12. [Troubleshooting](#troubleshooting)

---

## Overview

Omarchy is installed **on top of** a base Arch Linux installation. The general process is:

1. Install base Arch Linux using the official installation ISO
2. Run the Omarchy installer script to apply the beautiful desktop environment

---

## Pre-Installation Requirements

### Hardware Requirements
- x86_64-compatible machine
- Minimum 512 MiB RAM (2+ GiB recommended)
- At least 30 GiB disk space
- Internet connection

### Download the Arch Linux ISO
```bash
# Download from: https://archlinux.org/download/
# Verify signature:
pacman-key -v archlinux-<version>-x86_64.iso.sig
```

### Create Bootable USB
```bash
# Using dd (replace /dev/sdX with your USB device)
sudo dd bs=4M if=archlinux-<version>-x86_64.iso of=/dev/sdX conv=fsync oflag=direct status=progress
```

---

## Booting the Installation Medium

1. **Disable Secure Boot** in BIOS/UEFI settings
2. Boot from the USB drive
3. Select "Arch Linux install medium" and press Enter
4. You'll be logged in as root with a Zsh shell

### Verify Boot Mode (UEFI vs BIOS)
```bash
cat /sys/firmware/efi/fw_platform_size
# Returns 64 = UEFI 64-bit mode
# Returns 32 = UEFI 32-bit mode
# "No such file or directory" = BIOS/Legacy mode
```

### Set Keyboard Layout (if needed)
```bash
loadkeys de-latin1  # Example: German keyboard
# List available layouts:
localectl list-keymaps
```

### Connect to Internet
```bash
# Wired: Should work automatically via DHCP
# Wireless:
iwctl
> station wlan0 scan
> station wlan0 get-networks
> station wlan0 connect <SSID>
> exit

# Verify connection
ping -c 3 archlinux.org
```

### Sync System Clock
```bash
timedatectl set-ntp true
timedatectl status
```

---

## Disk Partitioning

### Identify Your Disk
```bash
fdisk -l
lsblk
# Common devices: /dev/sda, /dev/nvme0n1, /dev/mmcblk0
```

### Partition Layout (UEFI with GPT - Recommended)

| Mount Point | Partition | Type | Size |
|-------------|-----------|------|------|
| `/boot` | `/dev/nvme0n1p1` | EFI System (ef00) | 1 GiB |
| `[SWAP]` | `/dev/nvme0n1p2` | Linux swap (8200) | 4+ GiB (equal to RAM recommended) |
| `/` | `/dev/nvme0n1p3` | Linux filesystem (8300) | Remainder (min 25 GiB) |

### Create Partitions with `fdisk`
```bash
fdisk /dev/nvme0n1

# Commands inside fdisk:
g          # Create new GPT partition table

# EFI partition (1 GiB)
n          # New partition
1          # Partition number
<Enter>    # First sector (default)
+1G        # Size
t          # Change type
1          # Select partition 1
1          # EFI System type

# Swap partition (4 GiB or more)
n
2
<Enter>
+8G        # Example: 8 GiB swap
t
2
19         # Linux swap type

# Root partition (rest of disk)
n
3
<Enter>
<Enter>    # Use remaining space

w          # Write changes and exit
```

### Alternative: Using `gdisk` for GPT
```bash
gdisk /dev/nvme0n1
# Similar commands, use 'o' for new GPT table
```

---

## Formatting Partitions

### Format EFI System Partition
```bash
mkfs.fat -F 32 /dev/nvme0n1p1
```

### Initialize Swap
```bash
mkswap /dev/nvme0n1p2
```

### Format Root Partition (ext4)
```bash
mkfs.ext4 /dev/nvme0n1p3
```

### Alternative: Btrfs Root (recommended for snapshots)
```bash
mkfs.btrfs /dev/nvme0n1p3

# Create subvolumes (optional but recommended)
mount /dev/nvme0n1p3 /mnt
btrfs subvolume create /mnt/@
btrfs subvolume create /mnt/@home
btrfs subvolume create /mnt/@snapshots
umount /mnt
```

---

## Mounting the File Systems

### Standard ext4 Setup
```bash
# Mount root partition
mount /dev/nvme0n1p3 /mnt

# Create boot directory and mount EFI partition
mount --mkdir /dev/nvme0n1p1 /mnt/boot

# Enable swap
swapon /dev/nvme0n1p2
```

### Btrfs with Subvolumes
```bash
mount -o subvol=@,compress=zstd,noatime /dev/nvme0n1p3 /mnt
mkdir -p /mnt/{boot,home,.snapshots}
mount -o subvol=@home,compress=zstd,noatime /dev/nvme0n1p3 /mnt/home
mount -o subvol=@snapshots,compress=zstd,noatime /dev/nvme0n1p3 /mnt/.snapshots
mount /dev/nvme0n1p1 /mnt/boot
swapon /dev/nvme0n1p2
```

### Verify Mounts
```bash
lsblk -f
```

---

## Base System Installation

### Configure Mirrors (Optional)
```bash
# Edit mirrorlist for faster downloads
vim /etc/pacman.d/mirrorlist
# Or use reflector:
reflector --country US --age 12 --protocol https --sort rate --save /etc/pacman.d/mirrorlist
```

### Install Base System
```bash
pacstrap -K /mnt base linux linux-firmware
```

### Install Essential Packages
```bash
pacstrap -K /mnt \
    base-devel \
    git \
    vim nano \
    networkmanager \
    sudo \
    grub efibootmgr \
    amd-ucode     # For AMD CPUs
    # intel-ucode # For Intel CPUs
```

### Generate fstab
```bash
genfstab -U /mnt >> /mnt/etc/fstab
# Verify the fstab
cat /mnt/etc/fstab
```

### Chroot into the New System
```bash
arch-chroot /mnt
```

---

## System Configuration (Inside Chroot)

### Set Timezone
```bash
ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime
# Or find your timezone:
# ls /usr/share/zoneinfo/
hwclock --systohc
```

### Set Locale
```bash
# Edit locale.gen
vim /etc/locale.gen
# Uncomment: en_US.UTF-8 UTF-8

# Generate locales
locale-gen

# Set system locale
echo "LANG=en_US.UTF-8" > /etc/locale.conf
```

### Set Hostname
```bash
echo "omarchy-workstation" > /etc/hostname
```

### Configure Hosts File
```bash
cat >> /etc/hosts << EOF
127.0.0.1   localhost
::1         localhost
127.0.1.1   omarchy-workstation.localdomain omarchy-workstation
EOF
```

---

## Initramfs Configuration

The initramfs (initial RAM filesystem) is a temporary root filesystem loaded into memory during boot, used to load necessary drivers and mount the real root filesystem.

### Understanding mkinitcpio

The `mkinitcpio` tool creates the initramfs image. Configuration is in `/etc/mkinitcpio.conf`.

### Default Hooks (Order Matters!)
```bash
# View current configuration
cat /etc/mkinitcpio.conf

# Default HOOKS line:
HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block filesystems fsck)
```

### Hook Descriptions

| Hook | Purpose |
|------|---------|
| `base` | Essential utilities for any initramfs |
| `udev` | Device manager, auto-detects hardware |
| `autodetect` | Reduces initramfs size by detecting needed modules |
| `microcode` | Loads CPU microcode updates |
| `modconf` | Loads modprobe configuration |
| `kms` | Kernel Mode Setting for early graphics |
| `keyboard` | Keyboard support in early boot |
| `keymap` | Applies console keymap |
| `consolefont` | Applies console font |
| `block` | Block device support |
| `filesystems` | Filesystem drivers |
| `fsck` | Filesystem check utility |

### Special Hooks for Encryption/LVM

```bash
# For LUKS encryption, add 'encrypt' before 'filesystems':
HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block encrypt filesystems fsck)

# For LVM, add 'lvm2' before 'filesystems':
HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block lvm2 filesystems fsck)

# For both:
HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block encrypt lvm2 filesystems fsck)
```

### Regenerate Initramfs
```bash
# Regenerate all presets
mkinitcpio -P

# Or regenerate specific preset
mkinitcpio -p linux
```

### Include Additional Modules
```bash
# Edit /etc/mkinitcpio.conf
# Add modules to MODULES array:
MODULES=(btrfs nvme)  # Example for Btrfs and NVMe

# Then regenerate:
mkinitcpio -P
```

---

## Boot Loader Setup

### Option 1: GRUB (Most Compatible)

#### Install GRUB for UEFI
```bash
# Install packages
pacman -S grub efibootmgr

# Install GRUB to EFI partition
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB

# Generate GRUB configuration
grub-mkconfig -o /boot/grub/grub.cfg
```

#### GRUB with Encryption
```bash
# Edit /etc/default/grub
vim /etc/default/grub

# Add kernel parameters for encrypted root:
GRUB_CMDLINE_LINUX="cryptdevice=UUID=<UUID-of-LUKS-partition>:cryptroot root=/dev/mapper/cryptroot"

# Enable GRUB to decrypt
GRUB_ENABLE_CRYPTODISK=y

# Regenerate config
grub-mkconfig -o /boot/grub/grub.cfg
```

### Option 2: systemd-boot (Simpler, UEFI only)

```bash
# Install bootloader
bootctl install

# Create boot entry
cat > /boot/loader/entries/arch.conf << EOF
title   Arch Linux
linux   /vmlinuz-linux
initrd  /amd-ucode.img
initrd  /initramfs-linux.img
options root=UUID=<ROOT-UUID> rw
EOF

# Configure loader
cat > /boot/loader/loader.conf << EOF
default arch.conf
timeout 3
console-mode max
editor no
EOF
```

### Get UUID for Boot Configuration
```bash
blkid /dev/nvme0n1p3
# Copy the UUID value
```

---

## Enable Essential Services
```bash
# Network Manager
systemctl enable NetworkManager

# Set root password
passwd

# Create user account
useradd -m -G wheel -s /bin/bash yourusername
passwd yourusername

# Enable sudo for wheel group
EDITOR=vim visudo
# Uncomment: %wheel ALL=(ALL:ALL) ALL
```

---

## Exit and Reboot
```bash
# Exit chroot
exit

# Unmount all partitions
umount -R /mnt

# Reboot
reboot
```

**Remove the USB drive when prompted!**

---

## Installing Omarchy

After booting into your fresh Arch Linux installation:

### Connect to Internet
```bash
nmcli device wifi connect "<SSID>" password "<password>"
# Or for wired:
nmcli device connect eth0
```

### Install Omarchy
```bash
# The official Omarchy installation command
bash <(curl -sL https://omarchy.org/install)
```

This will install and configure:
- Hyprland (Wayland compositor)
- Custom theming and fonts
- Pre-configured applications
- Development tools

### Alternative: Clone and Install Manually
```bash
git clone https://github.com/basecamp/omarchy.git
cd omarchy
./install.sh
```

---

## Post-Installation

### Install AUR Helper (yay)
```bash
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si
```

### GPU Drivers

#### AMD
```bash
pacman -S mesa vulkan-radeon libva-mesa-driver
```

#### NVIDIA
```bash
pacman -S nvidia nvidia-utils nvidia-settings
```

#### Intel
```bash
pacman -S mesa vulkan-intel intel-media-driver
```

### Install Additional Software
```bash
# Browsers
pacman -S firefox chromium

# Development
pacman -S code neovim tmux docker

# Multimedia
pacman -S vlc mpv spotify-launcher
```

---

## Troubleshooting

### Boot Issues - Rescue from Live USB

```bash
# Boot from USB, mount partitions
mount /dev/nvme0n1p3 /mnt
mount /dev/nvme0n1p1 /mnt/boot
arch-chroot /mnt

# Fix bootloader
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg

# Regenerate initramfs
mkinitcpio -P
```

### "Failed to mount /boot" Error
```bash
# Check fstab entries
cat /etc/fstab
# Ensure UUIDs match actual partitions
blkid
```

### No Network After Boot
```bash
# Enable and start NetworkManager
systemctl enable --now NetworkManager
nmcli device wifi list
nmcli device wifi connect "<SSID>" password "<password>"
```

### Kernel Panic - "VFS: Unable to mount root fs"
- Verify root UUID in bootloader config
- Ensure correct filesystem modules are in initramfs
- Check HOOKS in `/etc/mkinitcpio.conf` includes `filesystems`

### GRUB Not Showing
```bash
# Boot from USB and reinstall GRUB
arch-chroot /mnt
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB --recheck
grub-mkconfig -o /boot/grub/grub.cfg
```

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| List block devices | `lsblk -f` |
| Show partition UUIDs | `blkid` |
| Check disk space | `df -h` |
| View boot log | `journalctl -b` |
| Check systemd services | `systemctl --failed` |
| Regenerate initramfs | `mkinitcpio -P` |
| Update GRUB config | `grub-mkconfig -o /boot/grub/grub.cfg` |
| List installed packages | `pacman -Q` |
| Update system | `pacman -Syu` |

---

## Additional Resources

- [Arch Wiki - Installation Guide](https://wiki.archlinux.org/title/Installation_guide)
- [Arch Wiki - mkinitcpio](https://wiki.archlinux.org/title/Mkinitcpio)
- [Arch Wiki - GRUB](https://wiki.archlinux.org/title/GRUB)
- [Omarchy GitHub](https://github.com/basecamp/omarchy)
- [Omarchy Discord](https://discord.gg/omarchy)

---

*Last updated: March 2026*

