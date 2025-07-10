"""Configuration management for the SLIT installer.

This module provides interactive configuration prompts, auto-detection,
file loading/saving, and comprehensive validation with corruption detection.
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
from typing import List, Optional, Tuple

from .exceptions import ValidationError
from .hardware import HardwareManager
from .input import confirm, password
from .logging import get_logger
from .models import NetworkConfig, SystemConfig
from .validation import (
    validate_drive_path,
    validate_hostname,
    validate_locale,
    validate_timezone,
    validate_username,
)


class ConfigurationManager:
    """Manages interactive configuration prompts and file operations."""

    def __init__(self, dry_run: bool = False) -> None:
        """Initialize configuration manager.

        Args:
            dry_run: If True, simulate operations without making changes
        """
        self.dry_run = dry_run
        self.logger = get_logger(__name__)
        self.hardware_manager = HardwareManager(dry_run=dry_run)

    def get_configuration(
        self, config_file: str = "install.conf", force_interactive: bool = False, non_interactive: bool = False
    ) -> SystemConfig:
        """Get system configuration from file or interactive prompts.

        Args:
            config_file: Path to configuration file
            force_interactive: Force interactive mode even if config exists
            non_interactive: Skip edit prompts, use config file as-is

        Returns:
            Complete system configuration

        Raises:
            ValidationError: If configuration is invalid or corrupted
        """
        if not force_interactive and os.path.exists(config_file):
            try:
                config = self._load_and_validate_config(config_file)
                
                # Skip edit prompt in non-interactive mode
                if non_interactive:
                    return config
                    
                if self._prompt_edit_config():
                    return self._interactive_configuration(existing_config=config)
                return config
            except ValidationError as e:
                self.logger.error(f"Configuration file corrupted: {e.message}")
                if non_interactive:
                    raise  # Don't prompt in non-interactive mode
                if self._prompt_delete_corrupted_config(config_file):
                    os.unlink(config_file)
                    self.logger.info("Corrupted configuration deleted")
                else:
                    raise

        return self._interactive_configuration()

    def _load_and_validate_config(self, config_file: str) -> SystemConfig:
        """Load and validate configuration file with corruption detection.

        Args:
            config_file: Path to configuration file

        Returns:
            Validated system configuration

        Raises:
            ValidationError: If file is corrupted or invalid
        """
        try:
            # Check file integrity
            self._validate_config_file_integrity(config_file)

            # Load configuration
            config = SystemConfig.load_from_file(config_file)

            # Validate configuration
            errors = config.validate()
            if errors:
                error_messages = [f"  - {error.field}: {error.message}" for error in errors]
                raise ValidationError(
                    f"Configuration validation failed:\n" + "\n".join(error_messages),
                    "configuration",
                    config_file,
                    "Valid configuration file",
                )

            self.logger.info(f"Configuration loaded successfully from {config_file}")
            return config

        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise ValidationError(
                f"Failed to load configuration file: {e}",
                "config_file",
                config_file,
                "Valid JSON configuration file",
            )

    def _validate_config_file_integrity(self, config_file: str) -> None:
        """Validate configuration file integrity.

        Args:
            config_file: Path to configuration file

        Raises:
            ValidationError: If file is corrupted
        """
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for empty file
            if not content.strip():
                raise ValidationError(
                    "Configuration file is empty",
                    "config_file",
                    config_file,
                    "Non-empty configuration file",
                )

            # Check for binary data
            try:
                content.encode("utf-8")
            except UnicodeDecodeError:
                raise ValidationError(
                    "Configuration file contains binary data",
                    "config_file",
                    config_file,
                    "Text configuration file",
                )

            # Check minimum length (should have some content)
            if len(content) < 10:
                raise ValidationError(
                    "Configuration file appears truncated",
                    "config_file",
                    config_file,
                    "Complete configuration file",
                )

        except OSError as e:
            raise ValidationError(
                f"Cannot read configuration file: {e}",
                "config_file",
                config_file,
                "Readable configuration file",
            )

    def _interactive_configuration(
        self, existing_config: Optional[SystemConfig] = None
    ) -> SystemConfig:
        """Interactive configuration prompts with auto-detection.

        Args:
            existing_config: Existing configuration to use as defaults

        Returns:
            Complete system configuration
        """
        self._display_header("SLIT Installer Configuration")

        # Auto-detect defaults
        detected = self._auto_detect_settings()

        # Use existing config or detected values as defaults
        defaults = existing_config or detected

        print("\nSystem Configuration")
        print("=" * 50)

        # Get basic system settings
        locale = self._prompt_locale(defaults.locale)
        timezone = self._prompt_timezone(defaults.timezone)
        
        # Get user account information in proper order
        user_fullname = self._prompt_user_fullname(defaults.user_fullname)
        username = self._prompt_username(defaults.username)
        sudo_nopasswd = self._prompt_sudo_nopasswd(defaults.sudo_nopasswd)
        hostname = self._prompt_hostname(defaults.hostname)

        # Get drive selection
        target_drive = self._prompt_drive_selection(defaults.target_drive)

        # Get network configuration
        network = self._prompt_network_configuration(defaults.network)

        # Get user password
        password = self._prompt_password()

        # Create configuration
        config = SystemConfig(
            target_drive=target_drive,
            locale=locale,
            timezone=timezone,
            user_fullname=user_fullname,
            username=username,
            hostname=hostname,
            network=network,
            user_password=password,
            sudo_nopasswd=sudo_nopasswd,
        )

        # Display summary and save
        self._display_configuration_summary(config)
        if self._prompt_save_configuration():
            config.save_to_file("install.conf")
            print("✓ Configuration saved to install.conf")

        return config

    def _auto_detect_settings(self) -> SystemConfig:
        """Auto-detect system settings.

        Returns:
            SystemConfig with detected defaults
        """
        self.logger.info("Auto-detecting system settings...")

        # Detect locale
        locale = self._detect_locale()

        # Detect timezone
        timezone = self._detect_timezone()

        # Detect network interface
        interface = self._detect_primary_interface()

        # Create default network config
        network = NetworkConfig(network_type="dhcp", interface=interface)

        return SystemConfig(
            locale=locale,
            timezone=timezone,
            network=network,
        )

    def _detect_locale(self) -> str:
        """Detect system locale.

        Returns:
            Detected locale or default
        """
        try:
            # Try environment variables
            for var in ["LC_ALL", "LC_CTYPE", "LANG"]:
                locale = os.environ.get(var, "")
                if locale and validate_locale(locale):
                    return locale

            # Try locale command
            result = subprocess.run(
                ["locale", "-a"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "en_US.utf8" in line.lower() or "en_us.utf-8" in line.lower():
                        return "en_US.UTF-8"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return "en_US.UTF-8"

    def _detect_timezone(self) -> str:
        """Detect system timezone.

        Returns:
            Detected timezone or default
        """
        try:
            # Try reading system timezone
            if os.path.exists("/etc/timezone"):
                with open("/etc/timezone", "r", encoding="utf-8") as f:
                    timezone = f.read().strip()
                    if validate_timezone(timezone):
                        return timezone

            # Try timedatectl
            result = subprocess.run(
                ["timedatectl", "show", "--property=Timezone", "--value"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                timezone = result.stdout.strip()
                if validate_timezone(timezone):
                    return timezone

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return "America/New_York"

    def _detect_primary_interface(self) -> str:
        """Detect primary network interface.

        Returns:
            Primary network interface name
        """
        try:
            # Get default route interface
            result = subprocess.run(
                ["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Parse output: "default via X.X.X.X dev interface ..."
                match = re.search(r"dev\s+(\S+)", result.stdout)
                if match:
                    return match.group(1)

            # Fallback: get first non-loopback interface
            result = subprocess.run(
                ["ip", "link", "show"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    match = re.search(r"^\d+:\s+(\S+):", line)
                    if match:
                        interface = match.group(1)
                        if interface != "lo" and not interface.startswith("lo"):
                            return interface

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return "eth0"

    def _prompt_locale(self, default: str) -> str:
        """Prompt for system locale.

        Args:
            default: Default locale value

        Returns:
            Selected locale
        """
        while True:
            prompt = f"System locale [{default}]: "
            locale = input(prompt).strip() or default

            if validate_locale(locale):
                return locale

            print(f"✗ Invalid locale format. Expected format: xx_XX.UTF-8")
            print("  Examples: en_US.UTF-8, de_DE.UTF-8, fr_FR.UTF-8")

    def _prompt_timezone(self, default: str) -> str:
        """Prompt for system timezone.

        Args:
            default: Default timezone value

        Returns:
            Selected timezone
        """
        while True:
            prompt = f"System timezone [{default}]: "
            timezone = input(prompt).strip() or default

            if validate_timezone(timezone):
                return timezone

            print(f"✗ Invalid timezone format. Expected format: Area/Location")
            print("  Examples: America/New_York, Europe/London, Asia/Tokyo")

    def _prompt_user_fullname(self, default: str) -> str:
        """Prompt for user's full name.

        Args:
            default: Default full name value

        Returns:
            User's full name
        """
        while True:
            default_display = default or "KDE User"
            prompt = f"User full name [{default_display}]: "
            fullname = input(prompt).strip() or default_display

            if fullname:
                return fullname

            print("✗ Full name is required")

    def _prompt_username(self, default: str) -> str:
        """Prompt for username.

        Args:
            default: Default username value

        Returns:
            Selected username
        """
        while True:
            prompt = f"Username{f' [{default}]' if default else ''}: "
            username = input(prompt).strip() or default

            if not username:
                print("✗ Username is required")
                continue

            if validate_username(username):
                return username

            print(f"✗ Invalid username '{username}'")
            print("  - Must start with letter or underscore")
            print("  - Can contain letters, numbers, underscore, hyphen")
            print("  - Cannot be a reserved system name")

    def _prompt_sudo_nopasswd(self, default: bool) -> bool:
        """Prompt for passwordless sudo access.

        Args:
            default: Default sudo setting

        Returns:
            True if passwordless sudo should be enabled
        """
        return confirm("Add user to passwordless sudo? ", default=default)

    def _prompt_hostname(self, default: str) -> str:
        """Prompt for hostname.

        Args:
            default: Default hostname value

        Returns:
            Selected hostname
        """
        while True:
            prompt = f"Hostname{f' [{default}]' if default else ''}: "
            hostname = input(prompt).strip() or default

            if not hostname:
                print("✗ Hostname is required")
                continue

            if validate_hostname(hostname):
                return hostname

            print(f"✗ Invalid hostname '{hostname}'")
            print("  - Can contain letters, numbers, hyphens")
            print("  - Cannot start or end with hyphen")
            print("  - Each part must be 1-63 characters")

    def _prompt_drive_selection(self, default: str) -> str:
        """Prompt for target drive selection with real hardware detection.

        Args:
            default: Default drive value

        Returns:
            Selected drive path
        """
        print("\nDrive Selection")
        print("-" * 20)

        # Enumerate available drives
        print("🔍 Detecting storage drives...")
        all_drives = self.hardware_manager.enumerate_drives(include_removable=False)
        
        if not all_drives:
            print("⚠️  No suitable drives detected")
            return self._prompt_manual_drive_entry(default)
        
        # Filter safe drives (no Windows by default)
        safe_drives = self.hardware_manager.filter_safe_drives(all_drives, show_windows=False)
        
        # Show all drives with safety information
        print("\nAvailable drives:")
        for i, drive in enumerate(all_drives, 1):
            status_icons = []
            if drive.has_windows:
                status_icons.append("🪟 Windows")
            if drive.is_removable:
                status_icons.append("📱 Removable")
            if drive.size_gb < 20:
                status_icons.append("⚠️  Too small")
                
            status_str = f" ({', '.join(status_icons)})" if status_icons else ""
            suitable = "✅" if drive in safe_drives else "❌"
            
            print(f"  {i}. {suitable} {drive}{status_str}")
        
        # Show Windows drives warning
        windows_drives = [d for d in all_drives if d.has_windows]
        if windows_drives:
            print(f"\n⚠️  {len(windows_drives)} drive(s) contain Windows installations")
            print("   Installing on these drives may destroy Windows!")
        
        # Get user selection
        while True:
            if default and validate_drive_path(default):
                prompt = f"Select drive (1-{len(all_drives)}) [{default}]: "
            else:
                prompt = f"Select drive (1-{len(all_drives)}): "
                
            choice = input(prompt).strip()
            
            # Handle default
            if not choice and default:
                return self._validate_drive_choice(default, all_drives)
            
            # Handle numeric selection
            try:
                selection = int(choice)
                if 1 <= selection <= len(all_drives):
                    selected_drive = all_drives[selection - 1]
                    return self._validate_drive_choice(selected_drive.path, all_drives)
                else:
                    print(f"✗ Please enter a number between 1 and {len(all_drives)}")
            except ValueError:
                print("✗ Please enter a valid number")

    def _validate_drive_choice(self, drive_path: str, all_drives: list) -> str:
        """Validate and confirm drive choice.

        Args:
            drive_path: Selected drive path
            all_drives: List of all available drives

        Returns:
            Confirmed drive path
        """
        drive = self.hardware_manager.get_drive_by_path(all_drives, drive_path)
        
        if not drive:
            print(f"✗ Drive {drive_path} not found")
            return ""
            
        # Check for Windows and confirm
        if drive.has_windows:
            print(f"\n⚠️  WARNING: {drive.path} contains a Windows installation!")
            print("   Installing on this drive will DESTROY Windows!")
            while True:
                confirm = input("   Continue anyway? (type 'yes' to confirm): ").strip().lower()
                if confirm == "yes":
                    break
                elif confirm in ["no", "n", ""]:
                    print("   Drive selection cancelled")
                    return ""
                else:
                    print("   Please type 'yes' to confirm or 'no' to cancel")
        
        print(f"✓ Selected drive: {drive}")
        return drive_path

    def _prompt_manual_drive_entry(self, default: str) -> str:
        """Fallback to manual drive entry if detection fails.

        Args:
            default: Default drive value

        Returns:
            Selected drive path
        """
        print("\n💭 Manual drive entry mode")
        print("   (Automatic detection unavailable)")
        
        while True:
            prompt = f"Enter drive path{f' [{default}]' if default else ''}: "
            drive = input(prompt).strip() or default

            if not drive:
                print("✗ Target drive is required")
                continue

            if validate_drive_path(drive):
                return drive

            print(f"✗ Invalid drive path '{drive}'")
            print("  - Must be a valid drive path (e.g., /dev/nvme0n1, /dev/sda)")

    def _prompt_network_configuration(self, default: NetworkConfig) -> NetworkConfig:
        """Prompt for network configuration.

        Args:
            default: Default network configuration

        Returns:
            Network configuration
        """
        print("\nNetwork Configuration")
        print("-" * 30)

        # Network type selection
        print("Network types:")
        print("  1. DHCP (automatic)")
        print("  2. Static IP")
        print("  3. Manual (configure after installation)")

        while True:
            current_type = {"dhcp": "1", "static": "2", "manual": "3"}.get(
                default.network_type, "1"
            )
            prompt = f"Network type [1-3, default {current_type}]: "
            choice = input(prompt).strip() or current_type

            if choice == "1":
                network_type = "dhcp"
                break
            elif choice == "2":
                network_type = "static"
                break
            elif choice == "3":
                network_type = "manual"
                break
            else:
                print("✗ Please enter 1, 2, or 3")

        # Interface
        interface = input(f"Network interface [{default.interface}]: ").strip() or default.interface

        # Create network config based on type
        if network_type == "dhcp":
            return NetworkConfig(network_type="dhcp", interface=interface)
        elif network_type == "static":
            return self._prompt_static_network(interface, default)
        else:  # manual
            return NetworkConfig(network_type="manual", interface=interface)

    def _prompt_static_network(self, interface: str, default: NetworkConfig) -> NetworkConfig:
        """Prompt for static network configuration.

        Args:
            interface: Network interface name
            default: Default network configuration

        Returns:
            Static network configuration
        """
        print("\nStatic Network Settings")
        print("-" * 25)

        # Get IP address
        while True:
            prompt = f"IP address{f' [{default.ip_address}]' if default.ip_address else ''}: "
            ip_address = input(prompt).strip() or default.ip_address

            if not ip_address:
                print("✗ IP address is required for static configuration")
                continue

            if self._validate_ip_input(ip_address):
                break

        # Get netmask
        netmask = input(f"Netmask [{default.netmask or '255.255.255.0'}]: ").strip()
        if not netmask:
            netmask = default.netmask or "255.255.255.0"

        # Get gateway
        while True:
            prompt = f"Gateway{f' [{default.gateway}]' if default.gateway else ''}: "
            gateway = input(prompt).strip() or default.gateway

            if not gateway:
                print("✗ Gateway is required for static configuration")
                continue

            if self._validate_ip_input(gateway):
                break

        # Get DNS servers
        dns_servers = input(f"DNS servers [{default.dns_servers or '8.8.8.8,8.8.4.4'}]: ").strip()
        if not dns_servers:
            dns_servers = default.dns_servers or "8.8.8.8,8.8.4.4"

        return NetworkConfig(
            network_type="static",
            interface=interface,
            ip_address=ip_address,
            netmask=netmask,
            gateway=gateway,
            dns_servers=dns_servers,
        )

    def _validate_ip_input(self, ip_str: str) -> bool:
        """Validate IP address input with user feedback.

        Args:
            ip_str: IP address string to validate

        Returns:
            True if valid
        """
        from .validation import validate_ip_address

        if validate_ip_address(ip_str):
            return True

        print(f"✗ Invalid IP address format: {ip_str}")
        print("  Example: 192.168.1.100")
        return False

    def _prompt_password(self) -> str:
        """Prompt for user password with confirmation.

        Returns:
            User password
        """
        print("\nUser Account")
        print("-" * 15)

        while True:
            user_password = password("User password: ", confirm=True)
            
            if not user_password:
                print("✗ Password cannot be empty")
                continue

            if len(user_password) < 8:
                print("✗ Password must be at least 8 characters long")
                continue

            return user_password

    def _display_configuration_summary(self, config: SystemConfig) -> None:
        """Display configuration summary.

        Args:
            config: System configuration to display
        """
        print("\n" + "=" * 60)
        print("CONFIGURATION SUMMARY")
        print("=" * 60)
        print(f"Target Drive:     {config.target_drive}")
        print(f"Locale:           {config.locale}")
        print(f"Timezone:         {config.timezone}")
        print()
        print("User Account:")
        print(f"  Full Name:      {config.user_fullname}")
        print(f"  Username:       {config.username}")
        print(f"  Passwordless sudo: {'Yes' if config.sudo_nopasswd else 'No'}")
        print(f"Hostname:         {config.hostname}")
        print(f"Filesystem:       {config.filesystem}")
        print(f"Swap Size:        {config.swap_size}")
        print()
        print("Network Configuration:")
        print(f"  Type:           {config.network.network_type}")
        print(f"  Interface:      {config.network.interface}")
        if config.network.network_type == "static":
            print(f"  IP Address:     {config.network.ip_address}")
            print(f"  Netmask:        {config.network.netmask}")
            print(f"  Gateway:        {config.network.gateway}")
            print(f"  DNS Servers:    {config.network.dns_servers}")
        print("=" * 60)

    def _prompt_edit_config(self) -> bool:
        """Prompt to edit existing configuration.

        Returns:
            True if user wants to edit
        """
        return confirm("Edit existing configuration? ", default=False)

    def _prompt_delete_corrupted_config(self, config_file: str) -> bool:
        """Prompt to delete corrupted configuration.

        Args:
            config_file: Path to corrupted configuration file

        Returns:
            True if user wants to delete
        """
        print(f"\nConfiguration file '{config_file}' is corrupted or invalid.")
        return confirm("Delete corrupted file and start fresh? ", default=False)

    def _prompt_save_configuration(self) -> bool:
        """Prompt to save configuration.

        Returns:
            True if user wants to save
        """
        return confirm("\nSave configuration for future use? ", default=True)

    def _display_header(self, title: str) -> None:
        """Display application header.

        Args:
            title: Header title
        """
        print("\n" + "=" * 60)
        print(f" {title:^58} ")
        print("=" * 60)
        print("Secure Linux Installation Tool")
        print("Interactive Configuration Setup")
        print()