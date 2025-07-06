# KDE Neon Installer - Utility Functions Specification

## Overview

This document defines all the utility functions, classes, and modules needed to implement the KDE Neon installer in any programming language. Each function includes parameters, return values, error handling, and GUI-ready design considerations.

## Core System Functions

### Command Execution System

#### `execute_command(command, description, options={})`
**Purpose**: Central command execution with logging, dry-run support, and error handling

**Parameters**:
- `command` (string/array): System command to execute
- `description` (string): Human-readable description for UI/logging
- `options` (dict):
  - `dry_run` (bool): If true, simulate execution
  - `capture_output` (bool): Return command output
  - `check_success` (bool): Raise error on non-zero exit
  - `timeout` (int): Command timeout in seconds
  - `cwd` (string): Working directory
  - `env` (dict): Environment variables
  - `input_data` (string): Data to send to stdin

**Returns**: 
```python
CommandResult:
  - success (bool): Whether command succeeded
  - exit_code (int): Process exit code
  - stdout (string): Standard output
  - stderr (string): Standard error
  - duration (float): Execution time in seconds
```

**Error Handling**: Raises `CommandExecutionError` on failure (if check_success=True)

**GUI Considerations**: Progress callbacks, real-time output streaming

---

#### `execute_command_with_progress(command, description, progress_callback=None)`
**Purpose**: Execute command with real-time progress reporting for GUI

**Parameters**:
- `command`, `description`: Same as execute_command
- `progress_callback` (function): Called with progress updates
  - Signature: `callback(current_step, total_steps, current_description)`

**GUI Integration**: Essential for responsive UI during long operations

---

### Logging System

#### `initialize_logging(log_file=None, level='INFO', console_output=True)`
**Purpose**: Set up comprehensive logging system

**Parameters**:
- `log_file` (string): Path to log file (auto-generated if None)
- `level` (string): Logging level (DEBUG, INFO, WARN, ERROR)
- `console_output` (bool): Enable console logging

**Features**:
- Timestamped entries
- Automatic log rotation
- Cleanup of old logs
- Multi-level filtering

---

#### `log(level, message, context={})`
**Purpose**: Write structured log entries

**Parameters**:
- `level` (string): Log level
- `message` (string): Log message
- `context` (dict): Additional context data

**GUI Considerations**: Log viewer integration, real-time log streaming

---

### Error Handling Framework

#### `class InstallerError(Exception)`
**Purpose**: Base exception class for installer errors

**Attributes**:
- `message` (string): Error description
- `error_code` (string): Unique error identifier
- `context` (dict): Error context data
- `recoverable` (bool): Whether error allows recovery
- `user_message` (string): User-friendly error description

---

#### `class ValidationError(InstallerError)`
**Purpose**: Configuration validation errors

**Additional Attributes**:
- `field` (string): Field that failed validation
- `invalid_value` (any): The invalid value
- `expected_format` (string): Description of expected format

---

#### `error_handler(error, context={})`
**Purpose**: Central error handling with recovery options

**Parameters**:
- `error` (Exception): The caught exception
- `context` (dict): Additional error context

**Returns**: `ErrorHandlingResult` with recovery actions

**GUI Considerations**: Error dialog generation, recovery option presentation

---

## Configuration Management

### Configuration Data Models

#### `class SystemConfig`
**Purpose**: Complete system configuration data structure

**Attributes**:
```python
SystemConfig:
  - target_drive (string): Selected drive path
  - locale (string): System locale (e.g., "en_US.UTF-8")
  - timezone (string): System timezone (e.g., "America/New_York")
  - username (string): Primary user account name
  - hostname (string): System hostname
  - swap_size (string): Swap size or "auto"
  - filesystem (string): Root filesystem type
  - network (NetworkConfig): Network configuration
  - user_password (string): User password (encrypted)
  - sudo_nopasswd (bool): Passwordless sudo access
```

**Methods**:
- `validate()`: Comprehensive validation
- `to_dict()`: Serialize to dictionary
- `from_dict(data)`: Deserialize from dictionary
- `save_to_file(path)`: Save configuration
- `load_from_file(path)`: Load configuration

---

#### `class NetworkConfig`
**Purpose**: Network configuration settings

**Attributes**:
```python
NetworkConfig:
  - network_type (string): "dhcp", "static", or "manual"
  - interface (string): Network interface name
  - ip_address (string): Static IP address
  - netmask (string): Subnet mask
  - gateway (string): Gateway IP
  - dns_servers (string): DNS server list
  - domain_search (string): Search domains
  - dns_suffix (string): DNS routing domains
```

**Methods**:
- `validate()`: Network-specific validation
- `to_systemd_config()`: Generate systemd-networkd config

---

### Configuration Processing Functions

#### `load_configuration(config_path=None)`
**Purpose**: Load and validate configuration file

**Parameters**:
- `config_path` (string): Path to config file (optional)

**Returns**: `SystemConfig` object or None

**Error Handling**: Raises `ValidationError` with comprehensive error list

**GUI Considerations**: Progress indication, error presentation

---

#### `save_configuration(config, config_path=None)`
**Purpose**: Save configuration to file

**Parameters**:
- `config` (SystemConfig): Configuration object
- `config_path` (string): Save path (optional)

**Security**: Sets appropriate file permissions (600)

---

#### `validate_configuration(config)`
**Purpose**: Comprehensive configuration validation

**Parameters**:
- `config` (SystemConfig): Configuration to validate

**Returns**: List of `ValidationError` objects (empty if valid)

**Validation Rules**:
- Drive path format and existence
- IP address format validation
- Username/hostname format compliance
- Network configuration completeness
- Cross-field consistency checks

---

#### `auto_detect_settings()`
**Purpose**: Automatically detect system settings

**Returns**: Partial `SystemConfig` with detected values

**Detection Methods**:
- Locale from GeoIP/system settings
- Timezone from GeoIP/system clock
- Keyboard layout from current settings
- Primary network interface
- System capabilities

---

## Hardware Detection & Management

### Drive Management

#### `class Drive`
**Purpose**: Represents a storage drive

**Attributes**:
```python
Drive:
  - path (string): Device path (e.g., "/dev/nvme0n1")
  - size_gb (int): Drive size in gigabytes
  - model (string): Drive model name
  - is_removable (bool): Whether drive is removable
  - has_windows (bool): Windows installation detected
  - partitions (list): List of Partition objects
  - health_status (string): Drive health information
```

**Methods**:
- `get_info()`: Refresh drive information
- `is_suitable_for_installation()`: Installation suitability check
- `detect_windows()`: Windows detection
- `__str__()`: Human-readable representation

---

#### `enumerate_drives(filter_type="nvme")`
**Purpose**: Discover available storage drives

**Parameters**:
- `filter_type` (string): Drive type filter ("nvme", "sata", "all")

**Returns**: List of `Drive` objects

**Features**:
- Hardware detection
- Removable drive filtering
- Drive health assessment
- Model information extraction

---

#### `select_drive(available_drives, force_mode=False, show_windows=False)`
**Purpose**: Interactive drive selection with safety checks

**Parameters**:
- `available_drives` (list): List of Drive objects
- `force_mode` (bool): Bypass Windows protection
- `show_windows` (bool): Show Windows drives

**Returns**: Selected `Drive` object

**Safety Features**:
- Windows detection and warnings
- Dual-boot protection
- User confirmation for destructive actions

**GUI Considerations**: Drive visualization, safety dialogs

---

### Windows Detection System

#### `detect_windows_on_drive(drive_path)`
**Purpose**: Comprehensive Windows detection on specific drive

**Parameters**:
- `drive_path` (string): Path to drive to check

**Returns**: `WindowsDetectionResult` object

**Detection Methods**:
```python
WindowsDetectionResult:
  - has_windows (bool): Windows detected
  - confidence_level (string): "high", "medium", "low"
  - detection_methods (list): Methods that found Windows
  - windows_version (string): Detected Windows version
  - boot_entries (list): Related EFI boot entries
```

**Detection Techniques**:
- EFI boot entry analysis
- NTFS partition scanning
- Windows directory structure detection
- Registry file detection
- Hibernation file detection

---

#### `get_windows_drives(drive_list)`
**Purpose**: Identify Windows drives from list

**Parameters**:
- `drive_list` (list): List of Drive objects

**Returns**: Tuple of (windows_drives, safe_drives)

---

### EFI Management

#### `class EfiEntry`
**Purpose**: Represents an EFI boot entry

**Attributes**:
```python
EfiEntry:
  - boot_id (string): EFI boot ID (e.g., "0006")
  - name (string): Entry name
  - device_path (string): EFI device path
  - drive_path (string): Associated drive path
  - is_windows (bool): Windows-related entry
  - is_kde (bool): KDE-related entry
```

**Methods**:
- `remove()`: Remove this EFI entry
- `parse_device_path()`: Extract drive information

---

#### `get_efi_entries(filter_pattern=None)`
**Purpose**: Query EFI boot entries

**Parameters**:
- `filter_pattern` (string): Optional filter (e.g., "KDE", "Windows")

**Returns**: List of `EfiEntry` objects

---

#### `manage_existing_kde_entries(target_drive, pre_install_entries)`
**Purpose**: Handle existing KDE entries with differential comparison

**Parameters**:
- `target_drive` (string): Current installation target
- `pre_install_entries` (list): Entries before installation

**Features**:
- Automatic target drive entry removal
- User choice for other drive entries
- Safety confirmation dialogs

**GUI Considerations**: Entry selection interface, confirmation dialogs

---

## User Interface System

### Input Functions

#### `get_user_input(prompt, default=None, input_type="text", validation=None)`
**Purpose**: Unified user input with validation

**Parameters**:
- `prompt` (string): Input prompt text
- `default` (any): Default value
- `input_type` (string): "text", "password", "confirm", "choice", "number"
- `validation` (function): Validation function

**Returns**: Validated user input

**Input Types**:
- `text`: Free text input with optional regex validation
- `password`: Hidden password input with confirmation
- `confirm`: Yes/no confirmation with single-key input
- `choice`: Selection from predefined options
- `number`: Numeric input with range validation

**GUI Considerations**: Adaptive widget creation, real-time validation

---

#### `get_choice_input(prompt, choices, default=None)`
**Purpose**: Multiple choice selection

**Parameters**:
- `prompt` (string): Selection prompt
- `choices` (list): Available choices
- `default` (any): Default selection

**Returns**: Selected choice

**GUI Considerations**: Radio buttons, dropdowns, list selection

---

#### `get_password_input(prompt, confirm=True)`
**Purpose**: Secure password input

**Parameters**:
- `prompt` (string): Password prompt
- `confirm` (bool): Require password confirmation

**Returns**: Validated password

**Security Features**:
- Hidden input
- Strength validation
- Confirmation matching
- Memory clearing

---

### Display Functions

#### `display_header(title, subtitle=None)`
**Purpose**: Show application header

**Parameters**:
- `title` (string): Main title
- `subtitle` (string): Optional subtitle

**GUI Considerations**: Styled headers, branding integration

---

#### `display_section(section_name)`
**Purpose**: Show section separator

**Parameters**:
- `section_name` (string): Section title

---

#### `display_status(status_type, message)`
**Purpose**: Show status messages

**Parameters**:
- `status_type` (string): "success", "error", "warning", "info"
- `message` (string): Status message

**GUI Considerations**: Colored messages, icons, notifications

---

#### `display_progress(current, total, description)`
**Purpose**: Show progress information

**Parameters**:
- `current` (int): Current step
- `total` (int): Total steps
- `description` (string): Current operation

**GUI Considerations**: Progress bars, percentage display

---

#### `display_summary(config)`
**Purpose**: Show configuration summary

**Parameters**:
- `config` (SystemConfig): Configuration to display

**GUI Considerations**: Formatted tables, collapsible sections

---

### Professional CLI Interface

#### `class CliInterface`
**Purpose**: Professional command-line interface manager

**Methods**:
- `initialize()`: Set up terminal environment
- `cleanup()`: Restore terminal state
- `get_terminal_size()`: Get current terminal dimensions
- `clear_screen()`: Clear terminal display
- `set_title(title)`: Set terminal title

**Features**:
- Color support detection
- Unicode symbol support
- Terminal capability detection
- Responsive layout adaptation

---

## Installation Engine

### Phase Management

#### `class InstallationPhase`
**Purpose**: Base class for installation phases

**Attributes**:
- `phase_number` (int): Phase identifier
- `phase_name` (string): Human-readable name
- `description` (string): Phase description
- `config` (SystemConfig): Installation configuration

**Methods**:
- `execute()`: Run the phase
- `validate_prerequisites()`: Check phase requirements
- `cleanup()`: Phase cleanup on error

---

#### `execute_installation_phases(config, progress_callback=None)`
**Purpose**: Execute complete 5-phase installation

**Parameters**:
- `config` (SystemConfig): Installation configuration
- `progress_callback` (function): Progress reporting

**Features**:
- Sequential phase execution
- Error handling and recovery
- Progress tracking
- Cleanup on failure

**GUI Considerations**: Phase visualization, progress tracking

---

### Phase-Specific Functions

#### `phase1_system_preparation(config)`
**Purpose**: System preparation and validation

**Operations**:
- UEFI verification
- Network connectivity check
- Package installation
- EFI state capture

---

#### `phase2_partitioning(config)`
**Purpose**: Drive partitioning and formatting

**Operations**:
- Partition table creation
- EFI and root partition creation
- Filesystem formatting
- Partition verification

---

#### `phase3_system_installation(config)`
**Purpose**: System file installation

**Operations**:
- Mount point setup
- System file transfer
- Swap file creation
- Kernel file installation

---

#### `phase4_bootloader_configuration(config)`
**Purpose**: Bootloader setup

**Operations**:
- Chroot environment setup
- GRUB installation and configuration
- EFI entry management
- fstab generation

---

#### `phase5_system_configuration(config)`
**Purpose**: System configuration

**Operations**:
- Locale and timezone setup
- Network configuration
- User account creation
- Package cleanup
- Addon script execution

---

## Network Configuration

### Network Setup Functions

#### `configure_dhcp_network(install_root, domain_search=None, dns_suffix=None)`
**Purpose**: Configure DHCP network settings

**Parameters**:
- `install_root` (string): Target system root
- `domain_search` (string): Search domains
- `dns_suffix` (string): DNS routing domains

**Features**:
- systemd-networkd configuration
- Domain search vs routing distinction
- Service enablement

---

#### `configure_static_network(install_root, network_config)`
**Purpose**: Configure static IP network settings

**Parameters**:
- `install_root` (string): Target system root
- `network_config` (NetworkConfig): Static network settings

**Features**:
- IP address validation
- CIDR conversion
- Gateway configuration
- DNS setup

---

#### `configure_manual_network(install_root)`
**Purpose**: Set up manual network configuration instructions

**Parameters**:
- `install_root` (string): Target system root

**Features**:
- Template generation
- Documentation creation
- Example configurations

---

#### `validate_network_config(network_config)`
**Purpose**: Validate network configuration

**Parameters**:
- `network_config` (NetworkConfig): Configuration to validate

**Returns**: List of validation errors

**Validation Rules**:
- IP address format
- Network/subnet consistency
- Required field presence
- Gateway reachability

---

## System Integration

### Filesystem Operations

#### `create_filesystem(device, fs_type="ext4", label=None)`
**Purpose**: Create filesystem on device

**Parameters**:
- `device` (string): Device path
- `fs_type` (string): Filesystem type
- `label` (string): Filesystem label

**Features**:
- Multiple filesystem support
- Progress reporting
- Error handling

---

#### `mount_filesystem(device, mount_point, fs_type=None, options=None)`
**Purpose**: Mount filesystem

**Parameters**:
- `device` (string): Device or image path
- `mount_point` (string): Mount location
- `fs_type` (string): Filesystem type hint
- `options` (list): Mount options

**Features**:
- Automatic mount point creation
- Mount option handling
- Error recovery

---

#### `unmount_filesystem(mount_point, force=False)`
**Purpose**: Unmount filesystem

**Parameters**:
- `mount_point` (string): Mount location
- `force` (bool): Force unmount

**Features**:
- Graceful unmounting
- Force unmount capability
- Process killing if needed

---

### Package Management

#### `update_package_database()`
**Purpose**: Update system package database

**Features**:
- Distribution detection
- Appropriate package manager usage
- Error handling

---

#### `install_packages(package_list, update_first=True)`
**Purpose**: Install system packages

**Parameters**:
- `package_list` (list): Packages to install
- `update_first` (bool): Update database first

**Features**:
- Batch installation
- Dependency resolution
- Progress reporting

---

#### `remove_packages(package_list)`
**Purpose**: Remove system packages

**Parameters**:
- `package_list` (list): Packages to remove

**Features**:
- Safe removal
- Dependency checking
- Configuration preservation

---

### User Management

#### `create_user_account(username, password, full_name=None, sudo_access=True)`
**Purpose**: Create system user account

**Parameters**:
- `username` (string): Username
- `password` (string): User password
- `full_name` (string): Full name (GECOS)
- `sudo_access` (bool): Grant sudo privileges

**Features**:
- Password hashing
- Home directory creation
- Group membership
- Shell configuration

---

#### `configure_sudo_access(username, passwordless=False)`
**Purpose**: Configure sudo access

**Parameters**:
- `username` (string): Target username
- `passwordless` (bool): Enable passwordless sudo

**Features**:
- sudoers configuration
- Security validation
- Backup creation

---

## Validation & Safety

### Input Validation

#### `validate_ip_address(ip_string)`
**Purpose**: Validate IP address format

**Parameters**:
- `ip_string` (string): IP address to validate

**Returns**: Boolean validity

**Features**:
- IPv4 validation
- Network address checking
- Range validation

---

#### `validate_username(username)`
**Purpose**: Validate Linux username

**Parameters**:
- `username` (string): Username to validate

**Returns**: Boolean validity

**Validation Rules**:
- Length limits
- Character restrictions
- Reserved name checking
- System compatibility

---

#### `validate_hostname(hostname)`
**Purpose**: Validate system hostname

**Parameters**:
- `hostname` (string): Hostname to validate

**Returns**: Boolean validity

**Features**:
- RFC compliance
- Length restrictions
- Character validation

---

#### `validate_locale(locale_string)`
**Purpose**: Validate locale format

**Parameters**:
- `locale_string` (string): Locale to validate

**Returns**: Boolean validity

**Features**:
- Format validation (xx_XX.UTF-8)
- Availability checking
- System support verification

---

### System Validation

#### `check_system_requirements()`
**Purpose**: Validate system meets installation requirements

**Returns**: `SystemRequirementsResult` object

**Checks**:
- UEFI boot mode
- Available memory
- Disk space
- Network connectivity
- Required tools availability

---

#### `check_uefi_boot()`
**Purpose**: Verify UEFI boot mode

**Returns**: Boolean UEFI status

**Features**:
- /sys/firmware/efi detection
- EFI variable access checking
- Boot mode verification

---

#### `check_network_connectivity(test_hosts=None)`
**Purpose**: Test internet connectivity

**Parameters**:
- `test_hosts` (list): Hosts to test (default: common DNS servers)

**Returns**: Connectivity status

**Features**:
- Multiple host testing
- Timeout handling
- DNS resolution testing

---

## Advanced Features

### Addon System

#### `class AddonScript`
**Purpose**: Represents an addon script

**Attributes**:
- `path` (string): Script file path
- `name` (string): Script name
- `description` (string): Script description
- `priority` (int): Execution priority

**Methods**:
- `execute(install_root)`: Run the script
- `validate()`: Check script validity

---

#### `discover_addon_scripts(addon_directory="./addons")`
**Purpose**: Find and validate addon scripts

**Parameters**:
- `addon_directory` (string): Directory to scan

**Returns**: List of `AddonScript` objects

**Features**:
- Script discovery
- Validation checking
- Priority sorting

---

#### `execute_addon_scripts(scripts, install_root, progress_callback=None)`
**Purpose**: Execute addon scripts in order

**Parameters**:
- `scripts` (list): List of AddonScript objects
- `install_root` (string): Target system root
- `progress_callback` (function): Progress reporting

**Features**:
- Sequential execution
- Error isolation
- Progress tracking
- Non-blocking failures

---

### Auto-Detection

#### `detect_timezone()`
**Purpose**: Auto-detect system timezone

**Returns**: Detected timezone string

**Detection Methods**:
- GeoIP lookup
- System clock analysis
- Hardware clock reading
- User preference detection

---

#### `detect_locale()`
**Purpose**: Auto-detect system locale

**Returns**: Detected locale string

**Detection Methods**:
- Current system locale
- GeoIP-based locale
- Keyboard layout analysis
- User environment variables

---

#### `calculate_optimal_swap_size()`
**Purpose**: Calculate optimal swap file size

**Returns**: Swap size in bytes

**Algorithm**:
- ≤2GB RAM: 2x RAM
- 2-8GB RAM: Equal to RAM  
- 8-32GB RAM: 8GB fixed
- >32GB RAM: 4GB minimal

---

## GUI-Ready Architecture

### Model-View-Controller Pattern

#### `class InstallerModel`
**Purpose**: Data model for installer state

**Attributes**:
- `config` (SystemConfig): Current configuration
- `drives` (list): Available drives
- `current_phase` (int): Installation phase
- `installation_state` (string): Current state

**Methods**:
- `notify_observers()`: Observer pattern implementation
- `save_state()`: Persist installer state
- `restore_state()`: Restore installer state

---

#### `class InstallerController`
**Purpose**: Business logic controller

**Methods**:
- `handle_drive_selection()`: Process drive selection
- `handle_config_change()`: Process configuration changes
- `start_installation()`: Begin installation process
- `cancel_installation()`: Cancel ongoing installation

---

### GUI Interface Abstractions

#### `class InstallationWizard`
**Purpose**: Multi-step installation wizard

**Methods**:
- `add_page()`: Add wizard page
- `next_page()`: Advance to next page
- `previous_page()`: Return to previous page
- `validate_current_page()`: Validate current input

---

#### `class ProgressDialog`
**Purpose**: Installation progress display

**Methods**:
- `set_phase()`: Update current phase
- `set_progress()`: Update progress percentage
- `set_status()`: Update status message
- `add_log_entry()`: Add log entry

---

### Event System

#### `class EventManager`
**Purpose**: Event-driven communication

**Methods**:
- `register_handler()`: Register event handler
- `emit_event()`: Emit event to handlers
- `unregister_handler()`: Remove event handler

**Events**:
- `ConfigurationChanged`
- `DriveSelected`
- `PhaseStarted`
- `PhaseCompleted`
- `InstallationError`
- `InstallationCompleted`

---

### Configuration Persistence

#### `class ConfigurationManager`
**Purpose**: Configuration state management

**Methods**:
- `auto_save()`: Automatic configuration saving
- `create_backup()`: Create configuration backup
- `restore_backup()`: Restore from backup
- `export_config()`: Export configuration
- `import_config()`: Import configuration

---

## Error Handling & Recovery

### Recovery System

#### `class RecoveryManager`
**Purpose**: Installation recovery and cleanup

**Methods**:
- `create_checkpoint()`: Create recovery checkpoint
- `rollback_to_checkpoint()`: Rollback installation
- `cleanup_partial_installation()`: Clean failed installation
- `repair_installation()`: Attempt installation repair

---

#### `handle_installation_failure(error, context)`
**Purpose**: Comprehensive failure handling

**Parameters**:
- `error` (Exception): The failure that occurred
- `context` (dict): Failure context

**Recovery Options**:
- Retry failed operation
- Skip non-critical operation
- Rollback to safe state
- Complete cleanup and exit

---

## Performance & Optimization

### Caching System

#### `class ResourceCache`
**Purpose**: Cache expensive operations

**Methods**:
- `cache_drive_info()`: Cache drive detection results
- `cache_network_tests()`: Cache connectivity tests
- `invalidate_cache()`: Clear cached data

---

### Async Operations

#### `class AsyncOperationManager`
**Purpose**: Manage background operations

**Methods**:
- `start_background_task()`: Start async operation
- `wait_for_completion()`: Wait for operation completion
- `cancel_operation()`: Cancel background operation

**Use Cases**:
- Network connectivity testing
- Drive scanning
- Package database updates
- Download operations

---

This comprehensive utility function specification provides everything needed to implement a robust, GUI-ready KDE Neon installer in any programming language. Each function is designed with proper error handling, validation, and extensibility in mind.