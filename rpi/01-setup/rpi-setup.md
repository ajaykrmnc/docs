# Raspberry Pi Setup

> Complete configuration for Raspberry Pi as the central data node with SSD storage and nginx.

**Previous:** [Network Configuration](./network-configuration.md) | **Next:** [CAP Theorem](../02-concepts/cap-theorem.md)

---

## Hardware Setup

### Components
- Raspberry Pi 4 (4GB+ RAM recommended)
- External SSD (USB 3.0 connection)
- Ethernet cable (recommended over WiFi)
- Quality power supply (5V 3A)

### SSD Connection

```
┌─────────────────┐
│  Raspberry Pi 4 │
│                 │
│  USB 3.0 ●──────┼──────► SSD (via USB-SATA adapter)
│                 │        /mnt/ssd
│  Ethernet ●─────┼──────► Router
│                 │
└─────────────────┘
```

---

## Initial OS Setup

### Flash Raspberry Pi OS

```bash
# Using Raspberry Pi Imager (recommended)
# Download from: https://www.raspberrypi.com/software/

# Or using dd (advanced)
sudo dd if=raspios.img of=/dev/sdX bs=4M status=progress
```

### First Boot Configuration

```bash
# Update system
sudo apt update && sudo apt full-upgrade -y

# Set hostname
sudo hostnamectl set-hostname rpi-sync

# Set timezone
sudo timedatectl set-timezone America/New_York  # Change to your timezone

# Enable SSH (if not already)
sudo systemctl enable ssh
sudo systemctl start ssh
```

---

## SSD Configuration

### Identify SSD

```bash
# List block devices
lsblk

# Example output:
# sda           8:0    0 500G  0 disk
# └─sda1        8:1    0 500G  0 part

# Get detailed info
sudo fdisk -l /dev/sda
```

### Format SSD (if needed)

⚠️ **WARNING: This will erase all data on the SSD**

```bash
# Create partition
sudo fdisk /dev/sda
# Commands: n (new), p (primary), 1, Enter, Enter, w (write)

# Format as ext4
sudo mkfs.ext4 -L "distributed-data" /dev/sda1
```

### Mount SSD

```bash
# Create mount point
sudo mkdir -p /mnt/ssd

# Get UUID
sudo blkid /dev/sda1
# Note the UUID

# Add to fstab for auto-mount
sudo nano /etc/fstab

# Add line:
UUID=your-uuid-here /mnt/ssd ext4 defaults,noatime 0 2

# Mount now
sudo mount -a

# Verify
df -h /mnt/ssd
```

### Set Permissions

```bash
# Create data directory
sudo mkdir -p /mnt/ssd/distributed-lab
sudo chown -R pi:pi /mnt/ssd/distributed-lab

# Create subdirectories
mkdir -p /mnt/ssd/distributed-lab/{data,logs,www,sync}
```

---

## nginx Configuration

### Install nginx

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
```

### Configure for Distributed Lab

```bash
sudo nano /etc/nginx/sites-available/distributed-lab
```

```nginx
server {
    listen 80;
    server_name rpi-sync.local;

    # Static files from SSD
    root /mnt/ssd/distributed-lab/www;
    index index.html;

    # API proxy (for future sync service)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }

    # Sync data endpoint
    location /sync/ {
        alias /mnt/ssd/distributed-lab/sync/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }

    # Health check
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/distributed-lab /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### Create Index Page

```bash
cat > /mnt/ssd/distributed-lab/www/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Distributed Lab - RPi Node</title></head>
<body>
    <h1>🖥️ Distributed Computing Lab</h1>
    <p>RPi Node Status: <strong>Online</strong></p>
    <ul>
        <li><a href="/sync/">Sync Directory</a></li>
        <li><a href="/api/status">API Status</a></li>
    </ul>
</body>
</html>
EOF
```

---

## Performance Optimization

### Boot from SSD (Optional)

For maximum performance, boot directly from SSD:

```bash
# Update bootloader
sudo rpi-eeprom-update -a

# Configure boot order in raspi-config
sudo raspi-config
# Advanced Options > Boot Order > USB Boot
```

### Memory Split

Reduce GPU memory for headless operation:

```bash
sudo raspi-config
# Performance Options > GPU Memory > 16
```

---

## Verification

```bash
# Check SSD
df -h /mnt/ssd

# Check nginx
curl http://localhost/health

# Check from other device
curl http://rpi-sync.local/health
```

---

**Next:** [CAP Theorem & Consistency Models →](../02-concepts/cap-theorem.md)

