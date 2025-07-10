"""Hardware detection and management for the SLIT installer.

This module provides drive enumeration, Windows detection, and hardware
validation functionality for safe system installation.
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import List, Optional, Tuple

from .exceptions import ValidationError
from .logging import get_logger
from .models import Drive, WindowsDetectionResult


class HardwareManager:
    """Manages hardware detection and drive enumeration."""

    def __init__(self, dry_run: bool = False) -> None:
        """Initialize hardware manager.

        Args:
            dry_run: If True, simulate operations without making changes
        """
        self.dry_run = dry_run
        self.logger = get_logger(__name__)

    def enumerate_drives(self, include_removable: bool = False) -> List[Drive]:
        """Enumerate available storage drives.

        Args:
            include_removable: Include removable drives in results

        Returns:
            List of detected drives
        """
        self.logger.info("Enumerating storage drives")
        
        if self.dry_run:
            return self._get_mock_drives()

        drives = []
        
        try:
            # Get all block devices
            result = subprocess.run(
                ["lsblk", "-dpno", "NAME,SIZE,MODEL,TYPE"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.error(f"lsblk failed: {result.stderr}")
                return drives

            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                parts = line.split()
                if len(parts) < 4:
                    continue
                    
                device_path = parts[0]
                size_str = parts[1]
                model = " ".join(parts[2:-1]) if len(parts) > 4 else parts[2]
                device_type = parts[-1]
                
                # Check removable status separately
                removable = self._check_removable(device_path)
                
                # Filter for actual drives (not partitions)
                if device_type != "disk":
                    continue
                    
                # Skip removable drives unless explicitly requested
                if removable and not include_removable:
                    continue
                    
                # Parse size (convert from human readable)
                size_gb = self._parse_size_to_gb(size_str)
                
                # Create drive object
                drive = Drive(
                    path=device_path,
                    size_gb=size_gb,
                    model=model,
                    is_removable=removable
                )
                
                # Check for Windows installation
                drive.has_windows = self._detect_windows_on_drive(drive.path)
                
                drives.append(drive)
                
        except subprocess.TimeoutExpired:
            self.logger.error("Drive enumeration timed out")
        except Exception as e:
            self.logger.error(f"Drive enumeration failed: {e}")
            
        self.logger.info(f"Found {len(drives)} suitable drives")
        return drives

    def _check_removable(self, device_path: str) -> bool:
        """Check if device is removable.

        Args:
            device_path: Device path to check

        Returns:
            True if device is removable
        """
        try:
            device_name = device_path.replace("/dev/", "")
            removable_path = f"/sys/class/block/{device_name}/removable"
            
            if os.path.exists(removable_path):
                with open(removable_path, 'r') as f:
                    return f.read().strip() == "1"
        except Exception:
            pass
            
        return False

    def _get_mock_drives(self) -> List[Drive]:
        """Get mock drives for dry-run testing.

        Returns:
            List of mock drives for testing
        """
        return [
            Drive(
                path="/dev/nvme0n1",
                size_gb=500,
                model="Samsung SSD 980 500GB",
                is_removable=False,
                has_windows=False
            ),
            Drive(
                path="/dev/nvme1n1", 
                size_gb=1000,
                model="WD Black SN750 1TB",
                is_removable=False,
                has_windows=True  # Mock Windows drive for testing
            ),
            Drive(
                path="/dev/sda",
                size_gb=250,
                model="Crucial MX250 250GB",
                is_removable=False,
                has_windows=False
            )
        ]

    def _parse_size_to_gb(self, size_str: str) -> int:
        """Parse lsblk size string to GB.

        Args:
            size_str: Size string like "500G", "1.5T", "256M"

        Returns:
            Size in gigabytes
        """
        size_str = size_str.upper().strip()
        
        # Extract number and unit
        match = re.match(r"^([\d.]+)([KMGT]?)$", size_str)
        if not match:
            return 0
            
        number = float(match.group(1))
        unit = match.group(2)
        
        # Convert to GB
        multipliers = {
            "": 1,       # Assume bytes if no unit
            "K": 1e-6,   # KB to GB  
            "M": 1e-3,   # MB to GB
            "G": 1,      # GB to GB
            "T": 1000    # TB to GB
        }
        
        return int(number * multipliers.get(unit, 1))

    def _detect_windows_on_drive(self, drive_path: str) -> bool:
        """Detect Windows installation on a drive.

        Args:
            drive_path: Path to drive to check

        Returns:
            True if Windows detected
        """
        if self.dry_run:
            # Mock Windows detection for testing
            return "nvme1n1" in drive_path
            
        try:
            # Check for NTFS partitions
            result = subprocess.run(
                ["blkid", "-o", "value", "-s", "TYPE", f"{drive_path}*"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "ntfs" in result.stdout.lower():
                self.logger.info(f"NTFS partition found on {drive_path}")
                return True
                
            # Check for Windows EFI entries
            if self._check_windows_efi_entries(drive_path):
                return True
                
        except Exception as e:
            self.logger.debug(f"Windows detection failed for {drive_path}: {e}")
            
        return False

    def _check_windows_efi_entries(self, drive_path: str) -> bool:
        """Check for Windows-related EFI boot entries.

        Args:
            drive_path: Drive path to check

        Returns:
            True if Windows EFI entries found
        """
        try:
            result = subprocess.run(
                ["efibootmgr", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False
                
            # Look for Windows entries that reference this drive
            for line in result.stdout.splitlines():
                if any(keyword in line.lower() for keyword in ["windows", "microsoft"]):
                    # Check if the entry references our drive
                    if drive_path.replace("/dev/", "") in line:
                        return True
                        
        except Exception as e:
            self.logger.debug(f"EFI check failed: {e}")
            
        return False

    def get_drive_by_path(self, drives: List[Drive], path: str) -> Optional[Drive]:
        """Get drive object by path.

        Args:
            drives: List of available drives
            path: Drive path to find

        Returns:
            Drive object if found, None otherwise
        """
        for drive in drives:
            if drive.path == path:
                return drive
        return None

    def filter_safe_drives(self, drives: List[Drive], show_windows: bool = False) -> List[Drive]:
        """Filter drives for safe installation.

        Args:
            drives: List of all drives
            show_windows: Whether to include Windows drives

        Returns:
            List of drives safe for installation
        """
        safe_drives = []
        
        for drive in drives:
            # Skip removable drives
            if drive.is_removable:
                continue
                
            # Skip too small drives (< 20GB)
            if drive.size_gb < 20:
                continue
                
            # Skip Windows drives unless explicitly requested
            if drive.has_windows and not show_windows:
                continue
                
            safe_drives.append(drive)
            
        return safe_drives

    def detect_windows_comprehensive(self, drive_path: str) -> WindowsDetectionResult:
        """Comprehensive Windows detection with confidence levels.

        Args:
            drive_path: Drive path to analyze

        Returns:
            Detailed Windows detection result
        """
        detection_methods = []
        windows_version = ""
        confidence = "low"
        
        if self.dry_run:
            # Mock comprehensive detection for testing
            if "nvme1n1" in drive_path:
                return WindowsDetectionResult(
                    has_windows=True,
                    confidence_level="high",
                    detection_methods=["NTFS filesystem", "Windows EFI entries"],
                    windows_version="Windows 11",
                    boot_entries=["Boot0001: Windows Boot Manager"]
                )
            else:
                return WindowsDetectionResult(
                    has_windows=False,
                    confidence_level="high",
                    detection_methods=["No Windows indicators found"]
                )

        # Check filesystem signatures
        if self._has_ntfs_partitions(drive_path):
            detection_methods.append("NTFS filesystem")
            confidence = "medium"
            
        # Check for Windows directories
        if self._has_windows_directories(drive_path):
            detection_methods.append("Windows directory structure")
            confidence = "high"
            
        # Check EFI boot entries
        efi_entries = self._get_windows_efi_entries(drive_path)
        if efi_entries:
            detection_methods.append("Windows EFI entries")
            confidence = "high"
            
        # Determine Windows version if detected
        if detection_methods:
            windows_version = self._detect_windows_version(drive_path)
            
        has_windows = len(detection_methods) > 0
        
        return WindowsDetectionResult(
            has_windows=has_windows,
            confidence_level=confidence,
            detection_methods=detection_methods,
            windows_version=windows_version,
            boot_entries=efi_entries
        )

    def _has_ntfs_partitions(self, drive_path: str) -> bool:
        """Check for NTFS partitions on drive."""
        try:
            result = subprocess.run(
                ["blkid", "-o", "value", "-s", "TYPE", f"{drive_path}*"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "ntfs" in result.stdout.lower()
        except Exception:
            return False

    def _has_windows_directories(self, drive_path: str) -> bool:
        """Check for Windows directory structure."""
        # This would require mounting partitions to check
        # For now, return False - implement when needed
        return False

    def _get_windows_efi_entries(self, drive_path: str) -> List[str]:
        """Get Windows-related EFI entries for this drive."""
        entries = []
        try:
            result = subprocess.run(
                ["efibootmgr", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if any(keyword in line.lower() for keyword in ["windows", "microsoft"]):
                        entries.append(line.strip())
                        
        except Exception:
            pass
            
        return entries

    def _detect_windows_version(self, drive_path: str) -> str:
        """Detect Windows version on drive."""
        # This would require mounting and checking registry/version files
        # For now, return generic version
        return "Windows (version unknown)"