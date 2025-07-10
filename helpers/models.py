"""Data models for the SLIT installer.

This module defines the core data structures used throughout the installer,
including configuration models and hardware representation classes.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .exceptions import ValidationError
from .validation import (
    validate_hostname,
    validate_ip_address,
    validate_locale,
    validate_username,
)


@dataclass
class NetworkConfig:
    """Network configuration settings.

    Attributes:
        network_type: "dhcp", "static", or "manual"
        interface: Network interface name
        ip_address: Static IP address
        netmask: Subnet mask
        gateway: Gateway IP
        dns_servers: DNS server list
        domain_search: Search domains
        dns_suffix: DNS routing domains
    """

    network_type: str = "dhcp"
    interface: str = "eth0"
    ip_address: str = ""
    netmask: str = ""
    gateway: str = ""
    dns_servers: str = ""
    domain_search: str = ""
    dns_suffix: str = ""

    def validate(self) -> List[ValidationError]:
        """Validate network configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.network_type not in ("dhcp", "static", "manual"):
            errors.append(
                ValidationError(
                    "Invalid network type",
                    "network_type",
                    self.network_type,
                    "dhcp, static, or manual",
                )
            )

        if self.network_type == "static":
            if not self.ip_address:
                errors.append(
                    ValidationError(
                        "IP address required for static configuration",
                        "ip_address",
                        self.ip_address,
                        "Valid IP address",
                    )
                )
            elif not validate_ip_address(self.ip_address):
                errors.append(
                    ValidationError(
                        "Invalid IP address format",
                        "ip_address",
                        self.ip_address,
                        "Valid IP address (e.g., 192.168.1.100)",
                    )
                )

            if not self.gateway:
                errors.append(
                    ValidationError(
                        "Gateway required for static configuration",
                        "gateway",
                        self.gateway,
                        "Valid gateway IP address",
                    )
                )
            elif not validate_ip_address(self.gateway):
                errors.append(
                    ValidationError(
                        "Invalid gateway IP address",
                        "gateway",
                        self.gateway,
                        "Valid IP address",
                    )
                )

        return errors

    def to_systemd_config(self) -> str:
        """Generate systemd-networkd configuration.

        Returns:
            systemd-networkd configuration string
        """
        config_lines = ["[Match]", f"Name={self.interface}", "", "[Network]"]

        if self.network_type == "dhcp":
            config_lines.append("DHCP=yes")
        elif self.network_type == "static":
            config_lines.extend(
                [
                    f"Address={self.ip_address}/{self._netmask_to_cidr()}",
                    f"Gateway={self.gateway}",
                ]
            )
            if self.dns_servers:
                config_lines.append(f"DNS={self.dns_servers}")

        if self.domain_search:
            config_lines.append(f"Domains={self.domain_search}")

        return "\n".join(config_lines)

    def _netmask_to_cidr(self) -> str:
        """Convert netmask to CIDR notation.

        Returns:
            CIDR prefix length
        """
        # Simple conversion for a common netmask
        netmask_map = {
            "255.255.255.0": "24",
            "255.255.0.0": "16",
            "255.0.0.0": "8",
            "255.255.255.128": "25",
            "255.255.255.192": "26",
            "255.255.255.224": "27",
            "255.255.255.240": "28",
            "255.255.255.248": "29",
            "255.255.255.252": "30",
        }
        return netmask_map.get(self.netmask, "24")


@dataclass
class SystemConfig:
    """Complete system configuration data structure.

    Attributes:
        target_drive: Selected drive path
        locale: System locale
        timezone: System timezone
        user_fullname: User's full name (GECOS field)
        username: Primary user account name
        hostname: System hostname
        swap_size: Swap size or "auto"
        filesystem: Root filesystem type
        network: Network configuration
        user_password: User password (encrypted)
        sudo_nopasswd: Passwordless sudo access
    """

    target_drive: str = ""
    locale: str = "en_US.UTF-8"
    timezone: str = "America/New_York"
    user_fullname: str = ""
    username: str = ""
    hostname: str = ""
    swap_size: str = "auto"
    filesystem: str = "ext4"
    network: NetworkConfig = field(default_factory=NetworkConfig)
    user_password: str = ""
    sudo_nopasswd: bool = False

    def validate(self) -> List[ValidationError]:
        """Comprehensive configuration validation.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate required fields
        if not self.target_drive:
            errors.append(
                ValidationError(
                    "Target drive is required",
                    "target_drive",
                    self.target_drive,
                    "Valid drive path (e.g., /dev/nvme0n1)",
                )
            )
        elif not self.target_drive.startswith("/dev/"):
            errors.append(
                ValidationError(
                    "Invalid drive path format",
                    "target_drive",
                    self.target_drive,
                    "Path starting with /dev/",
                )
            )

        if not self.user_fullname:
            errors.append(
                ValidationError(
                    "User full name is required",
                    "user_fullname",
                    self.user_fullname,
                    "User's full name",
                )
            )

        if not self.username:
            errors.append(
                ValidationError(
                    "Username is required",
                    "username",
                    self.username,
                    "Valid Linux username",
                )
            )
        elif not validate_username(self.username):
            errors.append(
                ValidationError(
                    "Invalid username format",
                    "username",
                    self.username,
                    "Lowercase letters, numbers, underscore, starting with letter",
                )
            )

        if not self.hostname:
            errors.append(
                ValidationError(
                    "Hostname is required", "hostname", self.hostname, "Valid hostname"
                )
            )
        elif not validate_hostname(self.hostname):
            errors.append(
                ValidationError(
                    "Invalid hostname format",
                    "hostname",
                    self.hostname,
                    "Letters, numbers, hyphens, no spaces",
                )
            )

        if not validate_locale(self.locale):
            errors.append(
                ValidationError(
                    "Invalid locale format",
                    "locale",
                    self.locale,
                    "Format: xx_XX.UTF-8",
                )
            )

        # Validate network configuration
        errors.extend(self.network.validate())

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "target_drive": self.target_drive,
            "locale": self.locale,
            "timezone": self.timezone,
            "user_fullname": self.user_fullname,
            "username": self.username,
            "hostname": self.hostname,
            "swap_size": self.swap_size,
            "filesystem": self.filesystem,
            "network": {
                "network_type": self.network.network_type,
                "interface": self.network.interface,
                "ip_address": self.network.ip_address,
                "netmask": self.network.netmask,
                "gateway": self.network.gateway,
                "dns_servers": self.network.dns_servers,
                "domain_search": self.network.domain_search,
                "dns_suffix": self.network.dns_suffix,
            },
            "user_password": self.user_password,
            "sudo_nopasswd": self.sudo_nopasswd,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SystemConfig:
        """Deserialize configuration from a dictionary.

        Args:
            data: Dictionary containing configuration data

        Returns:
            SystemConfig instance
        """
        network_data = data.get("network", {})
        network = NetworkConfig(
            network_type=network_data.get("network_type", "dhcp"),
            interface=network_data.get("interface", "eth0"),
            ip_address=network_data.get("ip_address", ""),
            netmask=network_data.get("netmask", ""),
            gateway=network_data.get("gateway", ""),
            dns_servers=network_data.get("dns_servers", ""),
            domain_search=network_data.get("domain_search", ""),
            dns_suffix=network_data.get("dns_suffix", ""),
        )

        return cls(
            target_drive=data.get("target_drive", ""),
            locale=data.get("locale", "en_US.UTF-8"),
            timezone=data.get("timezone", "America/New_York"),
            user_fullname=data.get("user_fullname", ""),
            username=data.get("username", ""),
            hostname=data.get("hostname", ""),
            swap_size=data.get("swap_size", "auto"),
            filesystem=data.get("filesystem", "ext4"),
            network=network,
            user_password=data.get("user_password", ""),
            sudo_nopasswd=data.get("sudo_nopasswd", False),
        )

    def save_to_file(self, file_path: str) -> None:
        """Save configuration to file.

        Args:
            file_path: Path to save a configuration file
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

        # Set appropriate file permissions (600)
        os.chmod(file_path, 0o600)

    @classmethod
    def load_from_file(cls, file_path: str) -> SystemConfig:
        """Load configuration from a file.

        Args:
            file_path: Path to a configuration file

        Returns:
            SystemConfig instance

        Raises:
            FileNotFoundError: If a file doesn't exist
            json.JSONDecodeError: If a file contains invalid JSON
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)


@dataclass
class Drive:
    """Represents a storage drive.

    Attributes:
        path: Device path (e.g., "/dev/nvme0n1")
        size_gb: Drive size in gigabytes
        model: Drive model name
        is_removable: Whether drive is removable
        has_windows: Windows installation detected
        partitions: List of partition information
        health_status: Drive health information
    """

    path: str
    size_gb: int
    model: str
    is_removable: bool = False
    has_windows: bool = False
    partitions: List[str] = field(default_factory=list)
    health_status: str = "unknown"

    def is_suitable_for_installation(self) -> bool:
        """Check if the drive is suitable for installation.

        Returns:
            True if the drive is suitable for installation
        """
        # Basic suitability checks
        if self.is_removable:
            return False

        if self.size_gb < 20:  # Minimum 20GB
            return False

        return True

    def __str__(self) -> str:
        """Human-readable representation of drive.

        Returns:
            String representation of drive
        """
        status = []
        if self.has_windows:
            status.append("Windows detected")
        if self.is_removable:
            status.append("Removable")

        status_str = f" ({', '.join(status)})" if status else ""
        return f"{self.path}: {self.model} - {self.size_gb}GB{status_str}"


@dataclass
class WindowsDetectionResult:
    """Result of Windows detection on a drive.

    Attributes:
        has_windows: Windows detected
        confidence_level: "high", "medium", "low"
        detection_methods: Methods that found Windows
        windows_version: Detected Windows version
        boot_entries: Related EFI boot entries
    """

    has_windows: bool
    confidence_level: str
    detection_methods: List[str] = field(default_factory=list)
    windows_version: str = ""
    boot_entries: List[str] = field(default_factory=list)


@dataclass
class EfiEntry:
    """Represents an EFI boot entry.

    Attributes:
        boot_id: EFI boot ID (e.g., "0006")
        name: Entry name
        device_path: EFI device path
        drive_path: Associated drive path
        is_windows: Windows-related entry
        is_slit: SLIT-related entry
    """

    boot_id: str
    name: str
    device_path: str
    drive_path: str = ""
    is_windows: bool = False
    is_slit: bool = False

    def __str__(self) -> str:
        """String representation of EFI entry.

        Returns:
            Human-readable EFI entry description
        """
        return f"Boot{self.boot_id}: {self.name}"
