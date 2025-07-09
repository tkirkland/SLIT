# SLIT Installer Function Reference

This document provides a comprehensive reference for all existing functions in the SLIT installer codebase, including parameter lists, return types, and usage examples.

## Table of Contents

- [Exception Classes](#exception-classes)
- [Data Models](#data-models)
- [Validation Functions](#validation-functions)
- [Command Execution](#command-execution)
- [Logging System](#logging-system)
- [Usage Examples](#usage-examples)

---

## Exception Classes

### InstallerError

Base exception class for all installer errors.

**Parameters:**
- `message: str` - Error description
- `error_code: str` - Unique error identifier
- `context: Optional[Dict[str, Any]] = None` - Error context data
- `recoverable: bool = False` - Whether error allows recovery
- `user_message: Optional[str] = None` - User-friendly error description

**Example:**

```python
from helpers.exceptions import InstallerError

try:
    # Some installer operation
    raise InstallerError(
        "Installation failed",
        "INSTALL_001",
        context={"phase": "preparation"},
        recoverable=True,
        user_message="Please check system requirements"
    )
except InstallerError as e:
    print(f"Error: {e.user_message}")
    print(f"Code: {e.error_code}")
    print(f"Recoverable: {e.recoverable}")
```

### ValidationError

Configuration validation specific errors.

**Parameters:**
- `message: str` - Error description
- `field: str` - Field that failed validation
- `invalid_value: Any` - The invalid value
- `expected_format: str` - Description of expected format
- `**kwargs` - Additional InstallerError arguments

**Example:**

```python
from helpers.exceptions import ValidationError

error = ValidationError(
    "Invalid IP address format",
    field="ip_address",
    invalid_value="192.168.1.999",
    expected_format="Valid IP address (e.g., 192.168.1.100)"
)
```

---

## Data Models

### NetworkConfig

Network configuration settings management.

#### validate()

**Parameters:** `self`  
**Returns:** `List[ValidationError]`  
**Description:** Validates network configuration settings

**Example:**

```python
from helpers.models import NetworkConfig

config = NetworkConfig(
    network_type="static",
    interface="eth0",
    ip_address="192.168.1.100",
    netmask="255.255.255.0",
    gateway="192.168.1.1",
    dns_servers="8.8.8.8,8.8.4.4"
)

errors = config.validate()
if errors:
    for error in errors:
        print(f"Validation error: {error.message}")
else:
    print("Network configuration is valid")
```

#### to_systemd_config()

**Parameters:** `self`  
**Returns:** `str`  
**Description:** Generates systemd-networkd configuration string

**Example:**
```python
config = NetworkConfig(network_type="dhcp", interface="enp0s3")
systemd_config = config.to_systemd_config()
print(systemd_config)
# Output:
# [Match]
# Name=enp0s3
# 
# [Network]
# DHCP=yes
```

### SystemConfig

Complete system configuration management.

#### validate()

**Parameters:** `self`  
**Returns:** `List[ValidationError]`  
**Description:** Comprehensive configuration validation

**Example:**

```python
from helpers.models import SystemConfig, NetworkConfig

config = SystemConfig(
    target_drive="/dev/nvme0n1",
    locale="en_US.UTF-8",
    timezone="America/New_York",
    username="user",
    hostname="slit-system",
    network=NetworkConfig(network_type="dhcp")
)

errors = config.validate()
if not errors:
    print("System configuration is valid")
```

#### save_to_file() / load_from_file()

**save_to_file Parameters:** `self, file_path: str`  
**load_from_file Parameters:** `cls, file_path: str`  
**Returns:** `None` / `SystemConfig`

**Example:**
```python
# Save configuration
config.save_to_file("install.conf")

# Load configuration
loaded_config = SystemConfig.load_from_file("install.conf")
```

### Drive

Storage drive representation and validation.

#### is_suitable_for_installation()

**Parameters:** `self`  
**Returns:** `bool`  
**Description:** Checks if drive is suitable for installation

**Example:**

```python
from helpers.models import Drive

drive = Drive(
    path="/dev/nvme0n1",
    size_gb=500,
    model="Samsung SSD 980",
    is_removable=False,
    has_windows=False
)

if drive.is_suitable_for_installation():
    print(f"Drive {drive.path} is suitable for installation")
else:
    print(f"Drive {drive.path} is not suitable")

print(str(drive))  # Human-readable representation
```

---

## Validation Functions

All validation functions return `bool` (True if valid, False if invalid).

### validate_ip_address(ip_string: str)

**Example:**

```python
from helpers.validation import validate_ip_address

print(validate_ip_address("192.168.1.100"))  # True
print(validate_ip_address("192.168.1.999"))  # False
print(validate_ip_address("10.0.0.1"))  # True
```

### validate_username(username: str)

**Example:**

```python
from helpers.validation import validate_username

print(validate_username("john"))  # True
print(validate_username("john123"))  # True
print(validate_username("123john"))  # False (can't start with number)
print(validate_username("root"))  # False (reserved name)
```

### validate_hostname(hostname: str)

**Example:**

```python
from helpers.validation import validate_hostname

print(validate_hostname("my-computer"))  # True
print(validate_hostname("server01"))  # True
print(validate_hostname("-invalid"))  # False (starts with hyphen)
print(validate_hostname("computer.local"))  # True
```

### validate_drive_path(drive_path: str)

**Example:**

```python
from helpers.validation import validate_drive_path

print(validate_drive_path("/dev/nvme0n1"))  # True
print(validate_drive_path("/dev/sda"))  # True
print(validate_drive_path("/home/user"))  # False
```

### validate_swap_size(swap_size: str)

**Example:**

```python
from helpers.validation import validate_swap_size

print(validate_swap_size("auto"))  # True
print(validate_swap_size("2G"))  # True
print(validate_swap_size("512M"))  # True
print(validate_swap_size("1024"))  # True (bytes)
print(validate_swap_size("huge"))  # False
```

---

## Command Execution

### execute_command()

**Parameters:**
- `command: Union[str, List[str]]` - System command to execute
- `description: str` - Human-readable description
- `capture_output: bool = True` - Return command output
- `check_success: bool = True` - Raise error on non-zero exit
- `timeout: Optional[int] = None` - Command timeout in seconds
- `cwd: Optional[str] = None` - Working directory
- `env: Optional[Dict[str, str]] = None` - Environment variables
- `input_data: Optional[str] = None` - Data to send to stdin

**Returns:** `CommandResult`

**Example:**

```python
from helpers.command import execute_command, set_dry_run_mode

# Enable dry run mode for testing
set_dry_run_mode(True)

# Execute a simple command
result = execute_command("ls -la", "List files in current directory")
print(f"Success: {result.success}")
print(f"Output: {result.stdout}")
print(f"Duration: {result.duration:.2f}s")

# Execute with custom environment
result = execute_command(
    ["echo", "$CUSTOM_VAR"],
    "Test environment variable",
    env={"CUSTOM_VAR": "Hello World"}
)

# Execute with timeout
try:
    result = execute_command(
        "sleep 10",
        "Long running command",
        timeout=5,
        check_success=True
    )
except CommandExecutionError as e:
    print(f"Command timed out: {e.message}")
```

### execute_command_with_progress()

**Example:**

```python
from helpers.command import execute_command_with_progress


def progress_callback(current, total, description):
    percentage = (current / total) * 100
    print(f"Progress: {percentage:.1f}% - {description}")


result = execute_command_with_progress(
    "apt update",
    "Updating package database",
    progress_callback=progress_callback
)
```

### CommandExecutor Class

**Example:**

```python
from helpers.command import CommandExecutor

# Create executor with dry run enabled
executor = CommandExecutor(dry_run=True)

# Execute commands through the executor
result = executor.execute_command(
    "sudo apt install -y python3",
    "Install Python 3"
)

# Use with progress reporting
result = executor.execute_command_with_progress(
    "wget https://example.com/file.iso",
    "Download ISO file",
    progress_callback=lambda c, t, d: print(f"{d}: {c}/{t}")
)
```

---

## Logging System

### initialize_logging()

**Parameters:**
- `log_file: Optional[str] = None` - Path to log file (auto-generated if None)
- `level: str = 'INFO'` - Logging level (DEBUG, INFO, WARN, ERROR)
- `console_output: bool = True` - Enable console logging
- `log_dir: Optional[str] = None` - Directory for log files

**Example:**

```python
from helpers.logging import initialize_logging, get_logger

# Initialize logging system
initialize_logging(
    level='DEBUG',
    console_output=True,
    log_dir='./logs'
)

# Get logger for your module
logger = get_logger(__name__)
logger.info("Logging system initialized")
```

### Logging Functions

**Example:**

```python
from helpers.logging import log_info, log_error, log_debug, log_warning

# Simple logging
log_info("Starting installation process")
log_error("Failed to mount filesystem")

# Logging with context
log_debug("Drive scan completed", context={
    "drives_found": 3,
    "nvme_drives": 2,
    "sata_drives": 1
})

# Warning with context
log_warning("Windows installation detected", context={
    "drive": "/dev/nvme0n1",
    "windows_version": "Windows 11"
})
```

### LogContext Class

**Example:**

```python
from helpers.logging import LogContext, get_logger

logger = get_logger(__name__)

# Use context manager to add context to all log messages
with LogContext({"installation_phase": "partitioning", "drive": "/dev/nvme0n1"}):
    logger.info("Starting partitioning")
    logger.debug("Creating EFI partition")
    logger.debug("Creating root partition")
    logger.info("Partitioning completed")
```

---

## Usage Examples

### Complete Installation Workflow Example

```python
#!/usr/bin/env python3
"""Example SLIT installer workflow."""

from helpers.logging import initialize_logging, get_logger
from helpers.models import SystemConfig, NetworkConfig
from helpers.command import set_dry_run_mode, execute_command
from helpers.validation import validate_drive_path
from helpers.exceptions import ValidationError, CommandExecutionError


def main():
    # Initialize logging
    initialize_logging(level='INFO', console_output=True)
    logger = get_logger(__name__)

    # Enable dry run for testing
    set_dry_run_mode(True)

    logger.info("Starting SLIT installation process")

    try:
        # Create system configuration
        network = NetworkConfig(
            network_type="dhcp",
            interface="enp0s3"
        )

        config = SystemConfig(
            target_drive="/dev/nvme0n1",
            locale="en_US.UTF-8",
            timezone="America/New_York",
            username="slit_user",
            hostname="slit-workstation",
            network=network
        )

        # Validate configuration
        logger.info("Validating configuration...")
        errors = config.validate()
        if errors:
            for error in errors:
                logger.error(f"Validation error: {error.message}")
            return 1

        # Validate drive path specifically
        if not validate_drive_path(config.target_drive):
            logger.error(f"Invalid drive path: {config.target_drive}")
            return 1

        logger.info("Configuration validation passed")

        # Save configuration
        config.save_to_file("slit_install.conf")
        logger.info("Configuration saved to slit_install.conf")

        # Example installation commands
        commands = [
            ("lsblk", "List available drives"),
            ("sudo fdisk -l", "Show partition tables"),
            (f"sudo parted {config.target_drive} mklabel gpt",
             "Create GPT partition table"),
        ]

        for cmd, desc in commands:
            try:
                result = execute_command(cmd, desc)
                logger.info(f"Command succeeded: {desc}")
            except CommandExecutionError as e:
                logger.error(f"Command failed: {desc} - {e.message}")
                return 1

        logger.info("Installation completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Installation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
```

### Configuration Management Example

```python
"""Example configuration management."""

from helpers.models import SystemConfig, NetworkConfig
from helpers.exceptions import ValidationError


def create_default_config():
    """Create a default system configuration."""
    network = NetworkConfig(network_type="dhcp")

    config = SystemConfig(
        target_drive="/dev/nvme0n1",
        username="user",
        hostname="slit-system",
        network=network
    )

    return config


def validate_and_save_config(config, filename):
    """Validate and save configuration."""
    errors = config.validate()
    if errors:
        print("Configuration errors found:")
        for error in errors:
            print(f"  - {error.field}: {error.message}")
        return False

    config.save_to_file(filename)
    print(f"Configuration saved to {filename}")
    return True


# Usage
config = create_default_config()
if validate_and_save_config(config, "default.conf"):
    print("Configuration is valid and saved")
```

### Error Handling Example

```python
"""Example error handling patterns."""

from helpers.exceptions import (
    ValidationError, CommandExecutionError,
    HardwareDetectionError, InstallerError
)
from helpers.command import execute_command
from helpers.logging import get_logger

logger = get_logger(__name__)


def handle_installation_errors():
    """Demonstrate error handling patterns."""
    try:
        # This might raise various exceptions
        result = execute_command("some_command", "Example operation")

    except ValidationError as e:
        logger.error(f"Validation failed for {e.field}: {e.message}")
        logger.info(f"Expected format: {e.expected_format}")
        return False

    except CommandExecutionError as e:
        logger.error(f"Command execution failed: {e.command}")
        logger.error(f"Exit code: {e.exit_code}")
        logger.error(f"Error output: {e.stderr}")

        if e.recoverable:
            logger.info("Error is recoverable, attempting retry...")
            # Implement retry logic
        return False

    except HardwareDetectionError as e:
        logger.error(f"Hardware detection failed: {e.message}")
        # Implement hardware detection fallback
        return False

    except InstallerError as e:
        logger.error(f"General installer error: {e.message}")
        logger.error(f"Error code: {e.error_code}")
        logger.error(f"Context: {e.context}")

        if e.user_message:
            print(f"User message: {e.user_message}")

        return False

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

    return True
```

---

## Function Summary

**Total Functions: 44**

- **Exception Classes**: 7 initialization methods
- **Data Models**: 8 methods for configuration and hardware management
- **Validation Functions**: 7 standalone validation functions
- **Command Execution**: 6 functions for system command execution
- **Logging System**: 16 functions for comprehensive logging and context management

All functions follow the Google Python Style Guide and include comprehensive type annotations, docstrings, and error handling.