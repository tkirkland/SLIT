# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a KDE Neon automated installer project featuring a comprehensive command-line installation system with advanced safety features, configuration management, and dual-boot protection.

## Development Environment

- **Target System**: KDE Neon live environment
- **Hardware**: UEFI systems with NVMe storage
- **Dependencies**: Standard Linux utilities, GRUB, systemd-networkd

## Project Architecture

This KDE Neon installer provides automated installation with extensive validation, configuration persistence, and safety mechanisms.

### Core Components

- **kde_neon_installer.sh**: Main installer script with 5-phase installation process
- **install.conf**: Configuration persistence file with comprehensive validation
- **logs/**: Timestamped installation logs for debugging and analysis

### Installation Process

The installer follows a structured approach:
1. **Configuration Management**: Load/validate saved settings or prompt for new configuration
2. **System Preparation**: Hardware validation, drive enumeration, Windows detection
3. **Partitioning**: EFI and root partition creation with proper alignment
4. **System Installation**: Filesystem creation, mounting, and system extraction
5. **Boot Configuration**: GRUB installation, EFI setup, boot entry management
6. **System Configuration**: Network setup, user creation, package cleanup

## Current Implementation Status

### ✅ Completed Features

**Configuration Management:**
- Interactive prompts with auto-detected defaults
- Configuration persistence in `install.conf`
- Comprehensive validation with corruption detection
- Edit mode with current values as defaults
- DNS settings for both DHCP and static network configurations

**Safety Features:**
- Windows installation detection for dual-boot protection
- NVMe drive enumeration and validation
- UEFI boot mode verification
- Boot entry management with conflict resolution
- Comprehensive error handling and logging

**Installation Process:**
- 5-phase structured installation
- Clean command output (installer messages only)
- Dry-run mode for testing
- User account creation with password validation
- Network configuration (DHCP, static, manual)
- Dynamic swap file sizing following modern best practices (≤2GB RAM: 2x, 2-8GB: equal, 8-32GB: 8GB, ≥32GB: 4GB)

**System Integration:**
- KDE Neon-specific package cleanup
- systemd-networkd configuration
- EFI boot entry naming ("KDE Neon")
- System clock configuration (local time)

### Configuration Validation System

The installer includes robust validation for configuration files:

**Syntax and Integrity:**
- Shell script syntax validation before sourcing
- File truncation detection (minimum line count)
- Binary data detection in text files

**Required Variables:**
- `network_config`, `locale`, `timezone` (target_drive detected dynamically)
- `username`, `hostname`, filesystem and swap settings (swap auto-calculated from RAM)

**Format Validation:**
- Drive paths: `/dev/nvmeXnY` pattern matching
- Network settings: IP address format validation
- Locale: `en_US.UTF-8` format compliance
- Timezone: `America/New_York` format validation
- Username: Linux username standards (lowercase, starting with letter)
- Hostname: Valid hostname format compliance

**Consistency Checks:**
- Static network configuration completeness
- Conflicting settings detection (manual network with static IP)
- Cross-field validation dependencies

**Recovery Mechanisms:**
- Automatic corruption detection on startup
- Detailed error listing with specific descriptions
- User choice to delete corrupted configurations
- Comprehensive logging of validation failures

## Development Guidelines

### Code Standards
- Use `execute_cmd` function for all system commands
- Redirect command output to log files (clean user interface)
- Implement comprehensive error handling with descriptive messages
- Follow existing logging patterns with timestamps

### Testing
- Always test with `--dry-run` mode first
- Test configuration validation with corrupted files
- Verify edit mode shows current defaults correctly
- Test all network configuration types (dhcp, static, manual)

### Security
- Validate all user inputs before use
- Use proper quoting for file paths and variables
- Hash passwords before storage
- Avoid exposing sensitive information in logs

## Future Development Priorities

### Enhanced Validation
- IP address range validation for static configurations
- Subnet mask compatibility checks with IP addresses
- Gateway reachability validation
- DNS server accessibility testing

### User Experience
- Progress indicators for long operations
- Better error recovery suggestions
- Configuration import/export functionality
- Installation resume capability

### Advanced Features
- Support for additional filesystems (btrfs, xfs)
- Multiple drive installation scenarios
- Enterprise network integration (domain joining)
- Full disk encryption support

### Code Quality
- Unit tests for validation functions
- Integration tests for installation phases
- Performance optimization for large operations
- Memory usage monitoring during installation

## Common Development Tasks

### Testing Configuration Validation
```bash
# Test with corrupted config
echo "invalid syntax here" > install.conf
sudo ./kde_neon_installer.sh --dry-run

# Test with missing variables
echo 'network_config="dhcp"' > install.conf
sudo ./kde_neon_installer.sh --dry-run
```

### Running Installation Tests
```bash
# Full dry-run test
sudo ./kde_neon_installer.sh --dry-run

# Test with custom config
sudo ./kde_neon_installer.sh --config test.conf --dry-run

# Test edit mode
sudo ./kde_neon_installer.sh --dry-run
# Choose "edit" when prompted
```

### Debugging
```bash
# Enable debug logging
export DEBUG=1
sudo ./kde_neon_installer.sh --dry-run

# Check validation logs
tail -f logs/kde-install-*.log | grep -E "(ERROR|WARN|Config validation)"
```

## Implementation Notes

### Configuration File Format
The `install.conf` file uses shell variable assignments:
```bash
target_drive="/dev/nvme0n1"
locale="en_US.UTF-8"
network_config="dhcp"
static_domain_search="local.lan example.com"
static_dns_suffix="corp.local"
```

### Network Configuration Types
- **dhcp**: Automatic IP with optional DNS settings
- **static**: Manual IP, gateway, DNS with required field validation
- **manual**: Post-installation manual configuration

### Validation Error Handling
All validation errors are collected and presented together, allowing users to see all issues at once rather than fixing them one by one.

### DNS Settings Application
DNS search domains and suffixes are applied to both DHCP and static network configurations using systemd-networkd `Domains=` entries.

---

This installer provides a robust, safe, and user-friendly way to install KDE Neon with comprehensive configuration management and validation.