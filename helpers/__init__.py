"""SLIT Installer Package.

This package provides a comprehensive command-line installation system with
advanced safety features, configuration management, and dual-boot protection
for SLIT systems.
"""

__version__ = "1.0.0"
__author__ = "SLIT Installer Team"

# Import main components for easy access
from .command import CommandExecutor, execute_command
from .config import ConfigurationManager
from .exceptions import InstallerError, ValidationError
from .hardware import HardwareManager
from .input import InputHandler, confirm, password, numeric, choice
from .logging import get_logger, initialize_logging
from .models import Drive, NetworkConfig, SystemConfig
from .validation import validate_hostname, validate_ip_address, validate_username

__all__ = [
    "CommandExecutor",
    "execute_command",
    "ConfigurationManager",
    "InstallerError",
    "ValidationError",
    "HardwareManager",
    "InputHandler",
    "confirm",
    "password",
    "numeric", 
    "choice",
    "get_logger",
    "initialize_logging",
    "Drive",
    "NetworkConfig", 
    "SystemConfig",
    "validate_hostname",
    "validate_ip_address",
    "validate_username",
]
