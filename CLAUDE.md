# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Required Reading for Context

**IMPORTANT**: Before working on any tasks, read these essential documentation files to understand the project structure and requirements:

1. **[README.md](README.md)** - Project overview, features, usage examples, and project structure
2. **[STYLE.md](STYLE.md)** - Google Python Style Guide compliance and code formatting standards
3. **[FUNCTION_REFERENCE.md](FUNCTION_REFERENCE.md)** - Complete reference for all existing functions, classes, and usage examples
4. **[UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md)** - Comprehensive specification for all utility functions and classes needed for implementation

These files contain critical information about:
- Project architecture and design patterns
- Existing code structure and helper modules
- Style guidelines and best practices
- Function signatures and implementation requirements
- TODO items and future development priorities

## Session Initialization

**CONTEXT LOADING**: When requested to load project context, read these files to establish full understanding:

1. **Use Read tool on these files in order:**
   - `README.md` - Project overview and current status
   - `STYLE.md` - Code formatting and style requirements  
   - `FUNCTION_REFERENCE.md` - Existing functions and usage patterns
   - `UTILITY_FUNCTIONS.md` - Implementation specifications
   - `requirements.txt` - Python dependencies
   - `SYSTEM_REQUIREMENTS.md` - System package requirements

2. **Check current project state:**
   - Run `git status` to understand current working state
   - Check `logs/` directory for recent installation logs
   - Review any TODO comments in `installer.py` and `helpers/` modules

3. **Establish development context:**
   - Understand current Python implementation status vs shell script reference
   - Identify immediate priorities from TODO items
   - Note any recent changes or development focus areas

This context loading ensures full project familiarity without rediscovering information through conversation.

## Project Overview

This is the **SLIT (Secure Linux Installation Tool)** project - a comprehensive automated installer system with advanced safety features, configuration management, and dual-boot protection. The project includes both shell script and Python implementations.

## Development Environment

- **Target System**: Linux live environments (KDE Neon, Ubuntu, etc.)
- **Hardware**: UEFI systems with NVMe storage
- **Dependencies**: Standard Linux utilities, GRUB, systemd-networkd
- **Python Version**: 3.8+ with type hints and modern features

## Project Architecture

SLIT provides automated installation with extensive validation, configuration persistence, and safety mechanisms through a 5-phase installation process.

### Core Components

**Shell Implementation:**
- **kde_neon_installer.sh**: Original shell script with complete 5-phase installation process
- **install.conf**: Configuration persistence file with comprehensive validation

**Python Implementation:**
- **installer.py**: Main Python installer with `SlitInstaller` class and phase-based architecture
- **helpers/**: Python package with command execution, logging, models, validation, and exceptions

**Common:**
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

## Python Implementation Status

### ✅ Completed Python Features

**Core Architecture:**
- `SlitInstaller` class with 5-phase orchestration
- `InstallationPhase` base class with common functionality
- All 5 phase classes implemented with stub methods
- Comprehensive dry-run support throughout
- Integration with existing `helpers/` modules

**Phase Structure:**
- `SystemPreparationPhase`: UEFI checks, network validation, package installation
- `PartitioningPhase`: GPT partitioning, EFI/root partition creation, formatting
- `SystemInstallationPhase`: Filesystem mounting, system file copying, swap creation
- `BootloaderConfigurationPhase`: Enhanced chroot setup, GRUB installation, fstab
- `SystemConfigurationPhase`: Locale/timezone, network, user creation, cleanup

**Enhanced Features:**
- Proper chroot environment with `/dev/pts`, tmpfs `/tmp`, EFI variables binding
- Type hints and comprehensive docstrings following Google Python Style Guide
- Error handling and logging integration
- TODO markers for all unimplemented functionality

### 🚧 Python TODO Items

**High Priority:**
- Implement squashfs detection and system file copying
- Add drive enumeration and Windows detection for dual-boot safety
- Implement configuration file loading and interactive prompts
- Add partition UUID detection and proper fstab generation
- Implement locale/timezone configuration and user account creation

**Medium Priority:**
- Add EFI boot entry cleanup functionality
- Implement systemd-networkd configuration for all network types
- Add kernel file installation from casper directory
- Implement package cleanup (remove live system packages)
- Add addon script execution support

**Future Enhancements:**
- Command-line argument parsing
- Progress reporting and GUI integration
- Enhanced error recovery and rollback capabilities

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

**Shell Script:**
```bash
# Full dry-run test
sudo ./kde_neon_installer.sh --dry-run

# Test with custom config
sudo ./kde_neon_installer.sh --config test.conf --dry-run

# Test edit mode
sudo ./kde_neon_installer.sh --dry-run
# Choose "edit" when prompted
```

**Python Implementation:**
```bash
# Test Python installer scaffold
python installer.py

# Run with custom configuration (when implemented)
# python installer.py --config test.conf --dry-run

# Test individual phases (when implemented)
# python -c "from installer import SystemPreparationPhase; ..."
```

### Debugging

**Shell Script:**
```bash
# Enable debug logging
export DEBUG=1
sudo ./kde_neon_installer.sh --dry-run

# Check validation logs
tail -f logs/kde-install-*.log | grep -E "(ERROR|WARN|Config validation)"
```

**Python Implementation:**
```bash
# Enable debug logging
python installer.py  # Uses INFO level by default

# Test with different log levels (when implemented)
# python installer.py --log-level DEBUG
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

## Recent Implementation Notes

- We are not updating the shell installer script. Its presence is to act as a guide to the flow that the python installer should follow as it works 100%, but with no zfs support

---

This installer provides a robust, safe, and user-friendly way to install KDE Neon with comprehensive configuration management and validation.