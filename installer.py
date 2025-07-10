#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SLIT Installer - Main installation orchestrator.

This module provides the main SLIT installer class that orchestrates
the 5-phase installation process with comprehensive safety features,
configuration management, and dual-boot protection.
"""

from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from typing import List  # TODO: Add Optional back when needed

from helpers.command import CommandExecutor

# TODO: Add back when implementing proper error handling
# from helpers.exceptions import InstallerError, ValidationError
from helpers.logging import get_logger, initialize_logging
from helpers.models import SystemConfig


class InstallationPhase(ABC):
    """Base class for all installation phases.

    Provides common functionality for phase execution, logging, and error handling.
    All specific phase implementations should inherit from this class.
    """

    def __init__(
        self,
        config: SystemConfig,
        command_executor: CommandExecutor,
        dry_run: bool = False,
    ) -> None:
        """Initialize the installation phase.

        Args:
            config: System configuration object
            command_executor: Command executor for system operations
            dry_run: If True, simulate operations without making changes
        """
        self.config = config
        self.command_executor = command_executor
        self.dry_run = dry_run
        self.logger = get_logger(self.__class__.__name__)
        self.phase_name = self.__class__.__name__.replace("Phase", "")
        self.install_root = "/target"

    def execute(self) -> bool:
        """Execute this installation phase.

        Returns:
            True if the phase is completed successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting {self.phase_name}")
            self._log_phase_start()

            success = self._execute_phase()

            if success:
                self.logger.info(f"Completed {self.phase_name}")
                self._log_phase_complete()
            else:
                self.logger.error(f"Phase failed: {self.phase_name}")

            return success

        except Exception as e:
            self.logger.error(f"Phase {self.phase_name} failed with exception: {e}")
            return False

    def _log_phase_start(self) -> None:
        """Log the start of the phase with appropriate formatting."""
        separator = "=" * 50
        if self.dry_run:
            print(f"\n[DRY-RUN] {separator}")
            print(f"[DRY-RUN] Starting {self.phase_name}")
            print(f"[DRY-RUN] {separator}")
        else:
            print(f"\n{separator}")
            print(f"Starting {self.phase_name}")
            print(f"{separator}")

    def _log_phase_complete(self) -> None:
        """Log the completion of the phase."""
        if self.dry_run:
            print(f"[DRY-RUN] {self.phase_name} completed successfully")
        else:
            print(f"{self.phase_name} completed successfully")

    @abstractmethod
    def _execute_phase(self) -> bool:
        """Execute the specific phase logic.

        This method must be implemented by each phase subclass.

        Returns:
            True if the phase is completed successfully, False otherwise
        """
        pass


class SystemPreparationPhase(InstallationPhase):
    """Phase 1: System preparation and validation.

    This phase performs initial system checks and preparation:
    - UEFI boot mode verification
    - Network connectivity check
    - Required package installation
    - System requirements validation

    TODO: Add Windows detection for dual-boot safety
    TODO: Add drive enumeration and selection
    TODO: Add EFI boot entry capture for cleanup
    """

    def _execute_phase(self) -> bool:
        """Execute system preparation phase."""
        if not self._check_uefi():
            return False

        if not self._check_network():
            return False

        if not self._install_required_packages():
            return False

        return True

    def _check_uefi(self) -> bool:
        """Verify UEFI boot mode is enabled."""
        self.logger.info("Checking UEFI boot mode")

        if self.dry_run:
            print("  [DRY-RUN] Would check /sys/firmware/efi directory")
            return True

        if not os.path.exists("/sys/firmware/efi"):
            self.logger.error("UEFI boot mode not detected")
            print("ERROR: UEFI boot mode required")
            return False

        print("   UEFI boot mode confirmed")
        return True

    def _check_network(self) -> bool:
        """Test network connectivity."""
        self.logger.info("Checking network connectivity")

        if self.dry_run:
            print("  [DRY-RUN] Would test network connectivity")
            return True

        # Use ping to test connectivity
        result = self.command_executor.execute_command(
            "ping -c 1 8.8.8.8", "Testing network connectivity"
        )

        if result.success:
            print("   Network connectivity confirmed")
            return True
        else:
            self.logger.error("Network connectivity test failed")
            print("ERROR: Network connection required")
            return False

    def _install_required_packages(self) -> bool:
        """Install required system packages."""
        self.logger.info("Installing required packages")

        packages = ["parted", "gdisk", "dosfstools", "e2fsprogs", "zfsutils-linux"]

        if self.dry_run:
            print(f"  [DRY-RUN] Would install packages: {', '.join(packages)}")
            return True

        # Update package database
        result = self.command_executor.execute_command(
            "apt-get -qq update", "Updating package database"
        )

        if not result.success:
            return False

        # Install packages
        result = self.command_executor.execute_command(
            f"apt-get -qq install -y {' '.join(packages)}",
            "Installing required packages",
        )

        return result.success


class PartitioningPhase(InstallationPhase):
    """Phase 2: Drive partitioning and formatting.

    This phase handles:
    - GPT partition table creation
    - EFI system partition creation
    - Root partition creation
    - Filesystem formatting

    TODO: Add partition alignment optimization
    TODO: Add support for different filesystem types
    TODO: Add partition validation and error recovery
    """

    def _execute_phase(self) -> bool:
        """Execute the partitioning phase."""
        drive = self.config.target_drive

        if not self._create_partition_table(drive):
            return False

        if not self._create_partitions(drive):
            return False

        if not self._format_partitions(drive):
            return False

        return True

    def _create_partition_table(self, drive: str) -> bool:
        """Create a GPT partition table."""
        self.logger.info(f"Creating GPT partition table on {drive}")

        if self.dry_run:
            print(f"  [DRY-RUN] Would create GPT partition table on {drive}")
            return True

        # Unmount any existing partitions
        self.command_executor.execute_command(
            f"umount {drive}p* 2>/dev/null || true", "Unmounting existing partitions"
        )

        # Create a GPT partition table
        result = self.command_executor.execute_command(
            f"parted -s {drive} mklabel gpt", "Creating GPT partition table"
        )

        return result.success

    def _create_partitions(self, drive: str) -> bool:
        """Create EFI and root partitions."""
        self.logger.info("Creating partitions")

        if self.dry_run:
            print("  [DRY-RUN] Would create EFI (512MB) and root partitions")
            return True

        # Create an EFI system partition (512MB)
        result = self.command_executor.execute_command(
            f"parted -s {drive} mkpart primary fat32 1MiB 513MiB",
            "Creating EFI system partition",
        )

        if not result.success:
            return False

        # Set EFI system partition flag
        result = self.command_executor.execute_command(
            f"parted -s {drive} set 1 esp on", "Setting EFI system partition flag"
        )

        if not result.success:
            return False

        # Create the root partition (remaining space)
        result = self.command_executor.execute_command(
            f"parted -s {drive} mkpart primary ext4 513MiB 100%",
            "Creating root partition",
        )

        return result.success

    def _format_partitions(self, drive: str) -> bool:
        """Format the created partitions."""
        self.logger.info("Formatting partitions")

        if self.dry_run:
            print("  [DRY-RUN] Would format EFI (FAT32) and root (ext4) partitions")
            return True

        # Wait for partition recognition
        result = self.command_executor.execute_command(
            f"partprobe {drive}", "Refreshing partition table"
        )

        if not result.success:
            return False

        # Format EFI partition
        result = self.command_executor.execute_command(
            f"mkfs.fat -F32 -n EFI {drive}p1", "Formatting EFI partition"
        )

        if not result.success:
            return False

        # Format root partition
        result = self.command_executor.execute_command(
            f"mkfs.ext4 -F -L ROOT {drive}p2", "Formatting root partition"
        )

        return result.success


class SystemInstallationPhase(InstallationPhase):
    """Phase 3: System file installation.

    This phase handles:
    - Filesystem mounting
    - System file copying from live environment
    - Swap file creation
    - Kernel file installation
    """

    def _execute_phase(self) -> bool:
        """Execute the system installation phase."""
        drive = self.config.target_drive

        if not self._mount_filesystems(drive):
            return False

        if not self._copy_system_files():
            return False

        if not self._create_swap_file():
            return False

        if not self._install_kernel_files():
            return False

        return True

    def _mount_filesystems(self, drive: str) -> bool:
        """Mount root and EFI filesystems."""
        self.logger.info("Mounting filesystems")

        if self.dry_run:
            print(f"  [DRY-RUN] Would mount {drive}p2 at {self.install_root}")
            print(f"  [DRY-RUN] Would mount {drive}p1 at {self.install_root}/boot/efi")
            return True

        # Create and mount root
        result = self.command_executor.execute_command(
            f"mkdir -p {self.install_root}", "Creating installation root"
        )

        if not result.success:
            return False

        result = self.command_executor.execute_command(
            f"mount {drive}p2 {self.install_root}", "Mounting root partition"
        )

        if not result.success:
            return False

        # Create and mount EFI
        result = self.command_executor.execute_command(
            f"mkdir -p {self.install_root}/boot/efi", "Creating EFI mount point"
        )

        if not result.success:
            return False

        result = self.command_executor.execute_command(
            f"mount {drive}p1 {self.install_root}/boot/efi", "Mounting EFI partition"
        )

        return result.success

    def _copy_system_files(self) -> bool:
        """Copy system files from a live environment."""
        self.logger.info("Copying system files")

        if self.dry_run:
            print("  [DRY-RUN] Would copy system files from squashfs")
            return True

        # TODO: Implement squashfs detection and mounting
        # TODO: Implement rsync system file copying with progress
        # TODO: Handle casper filesystem detection from multiple sources
        print("  Copying system files (this would take several minutes)")
        return True

    def _create_swap_file(self) -> bool:
        """Create the swap file."""
        self.logger.info("Creating swap file")

        swap_size = getattr(self.config, "swap_size", "4G")

        if self.dry_run:
            print(f"  [DRY-RUN] Would create {swap_size} swap file")
            return True

        result = self.command_executor.execute_command(
            f"fallocate -l {swap_size} {self.install_root}/swapfile",
            "Creating swap file",
        )

        if not result.success:
            return False

        result = self.command_executor.execute_command(
            f"chmod 600 {self.install_root}/swapfile", "Setting swap file permissions"
        )

        if not result.success:
            return False

        result = self.command_executor.execute_command(
            f"mkswap {self.install_root}/swapfile", "Formatting swap file"
        )

        return result.success

    def _install_kernel_files(self) -> bool:
        """Install kernel files."""
        self.logger.info("Installing kernel files")

        if self.dry_run:
            print("  [DRY-RUN] Would install kernel and initrd files")
            return True

        # TODO: Implement kernel version detection
        # TODO: Copy vmlinuz and initrd from casper directory
        # TODO: Handle multiple kernel source locations
        print("  Installing kernel files")
        return True


class BootloaderConfigurationPhase(InstallationPhase):
    """Phase 4: Bootloader configuration.

    This phase handles:
    - Chroot environment setup
    - GRUB installation
    - EFI boot entry management
    - fstab generation

    TODO: Add existing KDE boot entry cleanup
    TODO: Add systemd-boot entry removal
    TODO: Add initramfs update after GRUB configuration
    TODO: Add EFI variables binding in chroot
    """

    def _execute_phase(self) -> bool:
        """Execute the bootloader configuration phase."""
        if not self._setup_chroot():
            return False

        if not self._install_grub():
            return False

        if not self._configure_fstab():
            return False

        return True

    def _setup_chroot(self) -> bool:
        """Setup chroot environment."""
        self.logger.info("Setting up chroot environment")

        if self.dry_run:
            print("  [DRY-RUN] Would bind mount /proc, /sys, /dev, /dev/pts, /run")
            print("  [DRY-RUN] Would mount tmpfs on /tmp")
            print("  [DRY-RUN] Would bind mount EFI variables")
            return True

        # Bind mount essential filesystems
        bind_mounts = [
            ("/proc", f"{self.install_root}/proc"),
            ("/sys", f"{self.install_root}/sys"),
            ("/dev", f"{self.install_root}/dev"),
            ("/run", f"{self.install_root}/run"),
        ]

        for source, target in bind_mounts:
            result = self.command_executor.execute_command(
                f"mount --bind {source} {target}", f"Binding {source}"
            )
            if not result.success:
                return False

        # Mount /dev/pts for pseudo-terminal support
        result = self.command_executor.execute_command(
            f"mount --bind /dev/pts {self.install_root}/dev/pts", "Binding /dev/pts"
        )
        if not result.success:
            return False

        # Mount tmpfs for /tmp
        result = self.command_executor.execute_command(
            f"mount -t tmpfs tmpfs {self.install_root}/tmp", "Mounting tmpfs for /tmp"
        )
        if not result.success:
            return False

        # Set proper permissions on /tmp
        result = self.command_executor.execute_command(
            f"chmod 1777 {self.install_root}/tmp", "Setting proper permissions on /tmp"
        )
        if not result.success:
            return False

        # Bind mount EFI variables for GRUB installation
        result = self.command_executor.execute_command(
            f"mount --bind /sys/firmware/efi/efivars {self.install_root}/sys/firmware/efi/efivars",
            "Binding EFI variables",
        )
        if not result.success:
            return False

        return True

    def _install_grub(self) -> bool:
        """Install GRUB bootloader."""
        self.logger.info("Installing GRUB bootloader")

        drive = self.config.target_drive

        if self.dry_run:
            print(f"  [DRY-RUN] Would install GRUB on {drive}")
            return True

        # Install GRUB
        result = self.command_executor.execute_command(
            f"chroot {self.install_root} grub-install --target=x86_64-efi "
            f"--efi-directory=/boot/efi --bootloader-id='KDE Neon' {drive}",
            "Installing GRUB bootloader",
        )

        if not result.success:
            return False

        # Generate GRUB configuration
        result = self.command_executor.execute_command(
            f"chroot {self.install_root} update-grub", "Generating GRUB configuration"
        )

        return result.success

    def _configure_fstab(self) -> bool:
        """Configure fstab file."""
        self.logger.info("Configuring fstab")

        if self.dry_run:
            print("  [DRY-RUN] Would create /etc/fstab")
            return True

        # TODO: Get partition UUIDs using blkid
        # TODO: Generate proper fstab with root, EFI, and swap entries
        # TODO: Set proper mount options and filesystem check orders
        print("  Creating fstab configuration")
        return True


class SystemConfigurationPhase(InstallationPhase):
    """Phase 5: System configuration.

    This phase handles:
    - Locale and timezone configuration
    - Network configuration
    - User account creation
    - Package cleanup

    TODO: Add addon script execution support
    TODO: Add chroot filesystem unmounting
    TODO: Add hostname configuration
    TODO: Add system clock configuration (local time)
    """

    def _execute_phase(self) -> bool:
        """Execute system configuration phase."""
        if not self._configure_locale():
            return False

        if not self._configure_network():
            return False

        if not self._create_user_account():
            return False

        if not self._cleanup_packages():
            return False

        return True

    def _configure_locale(self) -> bool:
        """Configure system locale and timezone."""
        self.logger.info("Configuring locale and timezone")

        if self.dry_run:
            locale = getattr(self.config, "locale", "en_US.UTF-8")
            timezone = getattr(self.config, "timezone", "UTC")
            print(f"  [DRY-RUN] Would set locale to {locale}")
            print(f"  [DRY-RUN] Would set timezone to {timezone}")
            return True

        # TODO: Implement locale-gen and update-locale commands
        # TODO: Configure timezone with timedatectl
        # TODO: Set up /etc/timezone and /etc/localtime symlink
        print("  Configuring locale and timezone")
        return True

    def _configure_network(self) -> bool:
        """Configure network settings."""
        self.logger.info("Configuring network")

        if self.dry_run:
            network_type = getattr(self.config.network, "network_type", "dhcp")
            print(f"  [DRY-RUN] Would configure {network_type} network")
            return True

        # TODO: Implement systemd-networkd configuration
        # TODO: Handle DHCP, static, and manual network types
        # TODO: Configure DNS domains and search settings
        print("  Configuring network settings")
        return True

    def _create_user_account(self) -> bool:
        """Create the first (admin) user account."""
        self.logger.info("Creating user account")

        if self.dry_run:
            username = getattr(self.config, "username", "user")
            print(f"  [DRY-RUN] Would create user account: {username}")
            return True

        # TODO: Implement useradd with proper options
        # TODO: Set user password with chpasswd
        # TODO: Add user to sudo group and configure passwordless sudo
        # TODO: Set user full name and shell
        print("  Creating user account")
        return True

    def _cleanup_packages(self) -> bool:
        """Clean up live system packages."""
        self.logger.info("Cleaning up packages")

        if self.dry_run:
            print("  [DRY-RUN] Would remove live system packages")
            return True

        # TODO: Remove calamares, neon-live, casper packages
        # TODO: Run apt autoremove and autoclean
        # TODO: Clean up package cache
        print("  Cleaning up live system packages")
        return True


class SlitInstaller:
    """Main SLIT installer class.

    This class orchestrates the complete installation process through
    five distinct phases with comprehensive error handling and logging.
    """

    def __init__(self, config: SystemConfig, dry_run: bool = False) -> None:
        """Initialize the SLIT installer.

        Args:
            config: System configuration object
            dry_run: If True, simulate installation without making changes
        """
        self.config = config
        self.dry_run = dry_run
        self.command_executor = CommandExecutor(dry_run=dry_run)
        self.logger = get_logger(__name__)
        self.phases = self._initialize_phases()

    def _initialize_phases(self) -> List[InstallationPhase]:
        """Initialize all installation phases in order."""
        return [
            SystemPreparationPhase(self.config, self.command_executor, self.dry_run),
            PartitioningPhase(self.config, self.command_executor, self.dry_run),
            SystemInstallationPhase(self.config, self.command_executor, self.dry_run),
            BootloaderConfigurationPhase(
                self.config, self.command_executor, self.dry_run
            ),
            SystemConfigurationPhase(self.config, self.command_executor, self.dry_run),
        ]

    def install(self) -> bool:
        """Execute the complete installation process.

        Returns:
            True if installation is completed successfully, False otherwise
        """
        self.logger.info("Starting KDE Neon installation")

        if self.dry_run:
            print("=" * 60)
            print("DRY-RUN MODE: No actual changes will be made")
            print("=" * 60)

        # Validate configuration before starting
        errors = self.config.validate()
        if errors:
            self.logger.error("Configuration validation failed")
            for error in errors:
                self.logger.error(f"  - {error.message}")
            return False

        # Execute all phases
        for i, phase in enumerate(self.phases, 1):
            print(f"\n--- Phase {i} of {len(self.phases)} ---")

            if not phase.execute():
                self.logger.error(f"Installation failed at phase {i}")
                return False

        self.logger.info("Installation completed successfully")

        if self.dry_run:
            print("\n" + "=" * 60)
            print("DRY-RUN COMPLETED - No changes were made")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("🎉 SLIT Installation Complete! 🎉")
            print("=" * 60)

        return True


def main() -> int:
    """Main entry point for the installer.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Initialize logging
    initialize_logging(level="INFO", console_output=True)
    logger = get_logger(__name__)

    try:
        # TODO: Implement proper command-line argument parsing
        # TODO: Add configuration file loading and validation
        # TODO: Add interactive configuration prompts
        # TODO: Add drive selection with Windows detection
        # For now, create a basic configuration for testing
        from helpers.models import NetworkConfig, SystemConfig

        network_config = NetworkConfig(network_type="dhcp")
        config = SystemConfig(
            target_drive="/dev/nvme0n1",
            locale="en_US.UTF-8",
            timezone="UTC",
            username="user",
            hostname="slit-system",
            network=network_config,
        )

        # Test with dry-run mode
        installer = SlitInstaller(config, dry_run=True)

        if installer.install():
            print("\nInstaller scaffold test completed successfully!")
            return 0
        else:
            print("\nInstaller scaffold test failed!")
            return 1

    except Exception as e:
        logger.error(f"Installation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
