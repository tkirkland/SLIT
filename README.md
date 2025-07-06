# KDE Neon Automated Installer

A comprehensive command-line installer for KDE Neon systems with extensive hardware detection, dual-boot safety, and configuration management.

## Overview

This project provides a robust, automated installation system for KDE Neon with advanced features including NVMe drive detection, Windows dual-boot protection, comprehensive logging, and persistent configuration management. The installer follows a structured 5-phase approach ensuring reliable and safe system deployment.

## Features

### Automated Installation
- **Drive Enumeration**: Dynamic NVMe drive detection and selection
- **Dual-Boot Safety**: Windows installation detection to prevent accidental overwrites
- **Configuration Persistence**: Save and load installation preferences
- **Dry-Run Mode**: Test installations without making system changes
- **Comprehensive Logging**: Detailed logging for debugging and validation

### KDE Neon Integration
- **Helper Scripts**: Integration with KDE Neon-specific Calamares helpers
- **Package Management**: Intelligent cleanup of live system packages
- **System Configuration**: Proper locale, network, and boot configuration

## Quick Start

### Prerequisites
- UEFI-capable system
- NVMe storage device
- KDE Neon live environment
- Root privileges for installation

### Basic Usage

```bash
# Run with dry-run mode (recommended first run)
sudo ./kde_neon_installer.sh --dry-run

# Run actual installation with custom log path
sudo ./kde_neon_installer.sh --log-path /var/log/kde-install.log

# Use custom configuration file
sudo ./kde_neon_installer.sh --config /path/to/install.conf
```

## Project Structure

```
kde_script_install/
├── README.md                 # This file
├── CLAUDE.md                 # Project documentation and requirements
├── kde_neon_installer.sh     # Main installer script
├── install.conf             # Configuration file
├── logs/                    # Installation logs directory
│   └── kde-install-*.log    # Timestamped installation logs
└── .gitignore              # Git ignore rules
```

## Components

### Core Scripts

#### `kde_neon_installer.sh`
Main installer script that provides automated KDE Neon installation with comprehensive safety checks.

**Usage:**
```bash
sudo ./kde_neon_installer.sh [options]
```

**Features:**
- NVMe drive detection and enumeration
- Windows dual-boot protection
- Structured 5-phase installation process
- Comprehensive error handling and logging
- Configuration persistence and management

#### `install.conf`
Configuration file storing installation preferences and settings.

#### `logs/`
Directory containing timestamped installation logs for debugging and analysis.

### Installation Phases

The comprehensive installer follows a structured 5-phase approach:

1. **System Preparation**: Hardware validation, drive enumeration, Windows detection
2. **Partitioning**: EFI and root partition creation with proper alignment
3. **System Installation**: Filesystem creation, mounting, and file system extraction
4. **Bootloader Configuration**: GRUB installation, EFI setup, boot entry creation
5. **System Configuration**: Network setup, locale configuration, package cleanup

## Technical Requirements

### Hardware Support
- **Boot System**: UEFI-only (no legacy BIOS)
- **Storage**: NVMe drives only (`/dev/nvmeXXX`)
- **Security**: UEFI Secure Boot compatible
- **Memory**: Minimum 1GB RAM (dynamic swap file sizing based on available RAM)

### Software Dependencies
- KDE Neon live environment
- Calamares helper scripts (`/usr/bin/calamares-*`)
- Standard Linux utilities (blkid, mount, rsync, etc.)
- GRUB bootloader packages

### Supported Configurations
- **Partitioning**: Simple 2-partition scheme (EFI + root)
- **Filesystem**: ext4 for root, FAT32 for EFI
- **Swap**: File-based swap with RAM-based dynamic sizing (not partition)
- **Network**: systemd-networkd configuration
- **Boot**: Single-boot or dual-boot with Windows detection

## Configuration

### Initial Setup
On first run, the installer prompts for:
- Target drive selection
- User account information
- Locale and timezone settings
- Network configuration preferences
- Swap file sizing (with intelligent RAM-based defaults)

### Configuration Persistence
Settings are saved to `install.conf` in the script directory:
```ini
[system]
target_drive=/dev/nvme0n1
locale=en_US.UTF-8
timezone=America/New_York

[user]
username=user
hostname=kde-neon

[storage]
swap_size=8G  # Auto-calculated: ≤2GB RAM=2x, 2-8GB=equal, 8-32GB=8GB, ≥32GB=4GB
filesystem=ext4
```

### Configuration Validation
The installer includes comprehensive validation for configuration files:

**Corruption Detection:**
- **Syntax validation**: Checks for shell script syntax errors
- **File integrity**: Detects truncated or empty configuration files
- **Required variables**: Ensures all mandatory settings are present
- **Format validation**: Validates drive paths, IP addresses, locale formats, etc.
- **Consistency checks**: Detects conflicting settings (e.g., manual network with static IP)

**Automatic Recovery:**
- Detects corrupted configurations on startup
- Lists specific validation errors with clear descriptions
- Offers to delete corrupted files and start fresh
- Maintains detailed logs of validation failures

**Edit Mode Defaults:**
- When editing saved configurations, all prompts show current values as defaults
- Press Enter to keep existing values, or type new values to change them
- Ensures smooth configuration updates without re-entering all settings

### Command Line Options
```bash
Usage: kde_neon_installer.sh [options]

Options:
  --dry-run              Test mode - show what would be done
  --log-path PATH        Custom log file location
  --config PATH          Use custom configuration file
  --force                Skip safety checks (use with caution)
  --help                 Show this help message
```

## Safety Features

### Pre-Installation Validation
- **Hardware Compatibility**: UEFI and NVMe drive verification
- **Windows Detection**: Prevents accidental dual-boot overwrites
- **Drive Selection**: Internal drives only, excludes USB/external
- **Space Requirements**: Validates available storage space

### Dual-Boot Protection
- Automatically detects existing Windows installations
- Prompts for confirmation before modifying Windows drives
- Preserves EFI system partitions when possible
- Creates separate boot entries for each OS

### Boot Entry Management
- Automatically removes existing KDE entries on the target drive (prevents duplicates)
- Detects KDE entries on other drives and prompts user for removal decisions
- Shows drive information to help users identify legitimate vs. orphaned entries
- User controls removal of non-target-drive entries (safety first approach)

### Error Handling
- Comprehensive validation at each installation phase
- Rollback capability for failed operations
- Detailed error logging and reporting
- Safe exit on critical failures

## Development

### Contributing
1. Fork the repository
2. Create a feature branch
3. Test changes in a virtual environment
4. Submit pull request with detailed description

### Testing
```bash
# Test installer in dry-run mode
sudo ./kde_neon_installer.sh --dry-run

# Test with custom configuration
sudo ./kde_neon_installer.sh --config test_install.conf --dry-run

# Test with verbose logging
export DEBUG=1
sudo ./kde_neon_installer.sh --dry-run
```

### Architecture
- **Modular Design**: Separate functions for each installation phase
- **Error Recovery**: Graceful handling of installation failures
- **Logging**: Comprehensive logging for debugging and validation
- **Configuration**: Persistent settings and user preferences

## Future Development

### Planned Features
- **Enhanced Hardware**: Support for SATA drives and advanced partitioning
- **GUI Interface**: Graphical frontend for the command-line installer
- **Network Installation**: Remote installation and configuration management
- **Security**: Full disk encryption and advanced security features
- **Enterprise**: Integration with deployment systems and centralized management

### Roadmap
See [CLAUDE.md](CLAUDE.md) for detailed implementation tasks and future development items.

## Troubleshooting

### Common Issues

**Installer fails with "command not found"**
- Ensure kde_neon_installer.sh has execute permissions
- Verify running from correct directory
- Check bash version compatibility

**Installer fails drive detection**
- Confirm NVMe drives are present
- Check UEFI boot mode is enabled
- Verify drive permissions and accessibility

**Installation hangs or fails**
- Review installation logs for specific errors
- Check available disk space and memory
- Verify network connectivity for package downloads

### Debug Mode
Enable verbose logging:
```bash
export DEBUG=1
sudo ./kde_neon_installer.sh --dry-run
```

### Log Analysis
Installation logs are saved to:
- Default: `./logs/kde-install-YYYYMMDD-HHMMSS.log`
- Custom: Specified via `--log-path` option
- Logs contain detailed phase-by-phase installation progress
- Each log includes hardware detection, drive enumeration, and command execution details

## License

This project is released under the GPL-3.0 license, consistent with KDE and Calamares licensing.

## Acknowledgments

- **KDE Neon Team**: For the excellent distribution and Calamares configuration
- **Calamares Project**: For the modular installation framework
- **Community Contributors**: For testing, feedback, and improvements

---

For detailed technical documentation, see [CLAUDE.md](CLAUDE.md).