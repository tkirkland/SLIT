# SLIT System Requirements

This document outlines all system dependencies and requirements for the SLIT (Secure Linux Installation Tool) Python installer.

## Python Requirements

- **Python Version**: >= 3.8
- **Python Packages**: None (uses only standard library)
- **Type Hints**: Full type annotation support required

## Runtime Environment

- **Operating System**: Linux (Ubuntu/Debian-based distributions)
- **Architecture**: x86_64 (UEFI systems)
- **Privileges**: Root/sudo access required
- **Package Manager**: apt (Advanced Package Tool)

## System Package Dependencies

The following system packages are installed automatically during the installation process:

### Core Partitioning and Filesystem Tools
```bash
parted          # Disk partitioning operations
gdisk           # GPT partition table management
dosfstools      # FAT32 filesystem tools (mkfs.fat)
e2fsprogs       # ext4 filesystem tools (mkfs.ext4)
zfsutils-linux  # ZFS filesystem support (future use)
```

### Bootloader Components
```bash
grub-efi-amd64  # GRUB bootloader for UEFI systems
grub-pc-bin     # GRUB utilities and tools
efibootmgr      # EFI boot entry management
```

### System Utilities
```bash
util-linux      # mount, umount, fallocate, mkswap
coreutils       # chroot, basic system utilities
iputils-ping    # Network connectivity testing (ping)
```

### System Configuration
```bash
systemd         # systemd-networkd, systemd-resolved
locales         # Locale generation and configuration
tzdata          # Timezone data and configuration
```

## Installation Command

To install all required system packages:

```bash
sudo apt-get update
sudo apt-get install -y \
    parted \
    gdisk \
    dosfstools \
    e2fsprogs \
    zfsutils-linux \
    grub-efi-amd64 \
    grub-pc-bin \
    efibootmgr \
    util-linux \
    coreutils \
    iputils-ping \
    systemd \
    locales \
    tzdata
```

## Hardware Requirements

### Target System (Being Installed)
- **Storage**: NVMe SSD (recommended)
- **Boot Mode**: UEFI firmware
- **RAM**: Minimum 2GB (affects swap sizing)
- **Architecture**: x86_64

### Installation Environment
- **Live System**: Ubuntu/KDE Neon live environment
- **Network**: Internet connection for package installation
- **Display**: Terminal access (console or GUI terminal)

## File System Support

### Currently Supported
- **ext4**: Default root filesystem
- **FAT32**: EFI system partition
- **swap**: Swap files (dynamically sized)

### Future Support
- **ZFS**: ZFS pools and datasets (framework ready)
- **btrfs**: Btrfs subvolumes and snapshots
- **xfs**: XFS filesystems

## Network Requirements

### Installation Process
- **Internet Access**: Required for package installation
- **DNS Resolution**: Must be functional during installation
- **Package Repositories**: Access to Ubuntu/Debian repositories

### Target System Configuration
- **DHCP**: Automatic network configuration (default)
- **Static IP**: Manual network configuration support
- **DNS**: Custom DNS server configuration
- **Domain Search**: Custom domain search configuration

## Security Requirements

- **Secure Boot**: Compatible with UEFI Secure Boot
- **Permissions**: Proper file system permissions
- **Validation**: Input validation for all user data
- **Logging**: Comprehensive audit logging

## Development Environment

### Optional Development Dependencies
```bash
black>=25.1.0   # Code formatting
mypy>=1.0.0     # Type checking
pytest>=7.0.0   # Testing framework
```

### Development Setup
```bash
# Install development dependencies
pip install -e .[dev]

# Format code
black .

# Type checking
mypy installer.py helpers/

# Run tests (when implemented)
pytest
```

## Compatibility Notes

- **Minimum Python**: 3.8 for dataclass and typing features
- **Target Python**: 3.12+ for optimal performance
- **Live Environment**: Tested on KDE Neon and Ubuntu live systems
- **Package Versions**: Uses system package manager versions

## Performance Considerations

- **Memory Usage**: Low memory footprint (standard library only)
- **Disk I/O**: Optimized for SSD storage
- **Network**: Minimal network usage after package installation
- **CPU**: Low CPU requirements for installation process

---

*This document is updated as new requirements are identified during development.*