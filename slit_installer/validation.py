"""Input validation functions for the SLIT installer.

This module provides comprehensive validation functions for various input types
including IP addresses, usernames, hostnames, and locales.
"""

import re
from typing import Optional


def validate_ip_address(ip_string: str) -> bool:
    """Validate IP address format.

    Args:
        ip_string: IP address to validate

    Returns:
        True if IP address is valid, False otherwise
    """
    if not ip_string:
        return False

    # IPv4 validation
    ipv4_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    match = re.match(ipv4_pattern, ip_string)

    if not match:
        return False

    # Check each octet is in valid range (0-255)
    for octet in match.groups():
        if not (0 <= int(octet) <= 255):
            return False

    # Check it's not a network or broadcast address
    octets = [int(x) for x in match.groups()]

    # Avoid reserved ranges
    if octets[0] == 0 or octets[0] == 127:  # 0.x.x.x or 127.x.x.x
        return False

    if octets[0] >= 224:  # Multicast and reserved
        return False

    return True


def validate_username(username: str) -> bool:
    """Validate Linux username.

    Args:
        username: Username to validate

    Returns:
        True if username is valid, False otherwise
    """
    if not username:
        return False

    # Length limits (1-32 characters)
    if not (1 <= len(username) <= 32):
        return False

    # Must start with letter or underscore
    if not (username[0].isalpha() or username[0] == "_"):
        return False

    # Can contain letters, numbers, underscores, hyphens
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_-]*$", username):
        return False

    # Check for reserved usernames
    reserved_names = {
        "root",
        "bin",
        "daemon",
        "adm",
        "lp",
        "sync",
        "shutdown",
        "halt",
        "mail",
        "news",
        "uucp",
        "operator",
        "games",
        "gopher",
        "ftp",
        "nobody",
        "systemd-network",
        "systemd-resolve",
        "systemd-timesync",
        "messagebus",
        "systemd-coredump",
        "systemd-oom",
        "sshd",
        "chrony",
        "postfix",
        "tcpdump",
        "tss",
        "polkitd",
        "unbound",
        "sssd",
        "cockpit-ws",
        "cockpit-wsinstance",
        "setroubleshoot",
        "insights",
        "clevis",
        "pesign",
        "flatpak",
        "geoclue",
        "gnome-initial-setup",
        "saned",
        "colord",
        "avahi",
        "pulse",
        "gdm",
        "gnome-remote-desktop",
        "rpc",
        "gluster",
        "saslauth",
        "apache",
        "qemu",
        "kvm",
        "render",
        "pipewire",
        "rtkit",
        "test",
        "guest",
        "admin",
        "administrator",
        "user",
        "default",
    }

    if username.lower() in reserved_names:
        return False

    return True


def validate_hostname(hostname: str) -> bool:
    """Validate system hostname.

    Args:
        hostname: Hostname to validate

    Returns:
        True if hostname is valid, False otherwise
    """
    if not hostname:
        return False

    # Length restrictions (1-253 characters total)
    if not (1 <= len(hostname) <= 253):
        return False

    # Split into labels (parts separated by dots)
    labels = hostname.split(".")

    for label in labels:
        # Each label must be 1-63 characters
        if not (1 <= len(label) <= 63):
            return False

        # Must not start or end with hyphen
        if label.startswith("-") or label.endswith("-"):
            return False

        # Can only contain letters, numbers, hyphens
        if not re.match(r"^[a-zA-Z0-9-]+$", label):
            return False

        # Must not be all numeric (to avoid confusion with IP addresses)
        if label.isdigit():
            return False

    return True


def validate_locale(locale_string: str) -> bool:
    """Validate locale format.

    Args:
        locale_string: Locale to validate

    Returns:
        True if locale is valid, False otherwise
    """
    if not locale_string:
        return False

    # Format validation (xx_XX.UTF-8)
    locale_pattern = r"^[a-z]{2}_[A-Z]{2}\.UTF-8$"

    if not re.match(locale_pattern, locale_string):
        return False

    # Check for common valid locales
    valid_locales = {
        "en_US.UTF-8",
        "en_GB.UTF-8",
        "en_CA.UTF-8",
        "en_AU.UTF-8",
        "de_DE.UTF-8",
        "fr_FR.UTF-8",
        "es_ES.UTF-8",
        "it_IT.UTF-8",
        "pt_BR.UTF-8",
        "pt_PT.UTF-8",
        "ru_RU.UTF-8",
        "zh_CN.UTF-8",
        "zh_TW.UTF-8",
        "ja_JP.UTF-8",
        "ko_KR.UTF-8",
        "ar_SA.UTF-8",
        "hi_IN.UTF-8",
        "th_TH.UTF-8",
        "tr_TR.UTF-8",
        "pl_PL.UTF-8",
        "nl_NL.UTF-8",
        "sv_SE.UTF-8",
        "da_DK.UTF-8",
        "no_NO.UTF-8",
        "fi_FI.UTF-8",
        "cs_CZ.UTF-8",
        "hu_HU.UTF-8",
        "ro_RO.UTF-8",
        "bg_BG.UTF-8",
        "hr_HR.UTF-8",
        "sk_SK.UTF-8",
        "sl_SI.UTF-8",
        "et_EE.UTF-8",
        "lv_LV.UTF-8",
        "lt_LT.UTF-8",
        "uk_UA.UTF-8",
        "be_BY.UTF-8",
        "mk_MK.UTF-8",
        "mt_MT.UTF-8",
        "is_IS.UTF-8",
        "ga_IE.UTF-8",
        "cy_GB.UTF-8",
        "eu_ES.UTF-8",
        "ca_ES.UTF-8",
        "gl_ES.UTF-8",
        "oc_FR.UTF-8",
        "br_FR.UTF-8",
        "kw_GB.UTF-8",
        "gd_GB.UTF-8",
        "gv_GB.UTF-8",
    }

    # For now, accept any properly formatted locale
    # In a real implementation, you might check against system availability
    return True


def validate_timezone(timezone_string: str) -> bool:
    """Validate timezone format.

    Args:
        timezone_string: Timezone to validate

    Returns:
        True if timezone is valid, False otherwise
    """
    if not timezone_string:
        return False

    # Basic format validation (Area/Location)
    timezone_pattern = r"^[A-Z][a-zA-Z_]*\/[A-Z][a-zA-Z_]*$"

    if not re.match(timezone_pattern, timezone_string):
        return False

    # Check for common valid timezones
    valid_timezones = {
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Toronto",
        "America/Vancouver",
        "America/Mexico_City",
        "America/Sao_Paulo",
        "America/Argentina/Buenos_Aires",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Europe/Rome",
        "Europe/Madrid",
        "Europe/Amsterdam",
        "Europe/Brussels",
        "Europe/Vienna",
        "Europe/Warsaw",
        "Europe/Prague",
        "Europe/Budapest",
        "Europe/Zurich",
        "Europe/Stockholm",
        "Europe/Copenhagen",
        "Europe/Oslo",
        "Europe/Helsinki",
        "Europe/Moscow",
        "Europe/Kiev",
        "Europe/Bucharest",
        "Europe/Athens",
        "Europe/Istanbul",
        "Europe/Dublin",
        "Europe/Lisbon",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Asia/Hong_Kong",
        "Asia/Singapore",
        "Asia/Mumbai",
        "Asia/Kolkata",
        "Asia/Dubai",
        "Asia/Riyadh",
        "Asia/Seoul",
        "Asia/Taipei",
        "Asia/Bangkok",
        "Asia/Jakarta",
        "Asia/Manila",
        "Asia/Kuala_Lumpur",
        "Asia/Ho_Chi_Minh",
        "Australia/Sydney",
        "Australia/Melbourne",
        "Australia/Brisbane",
        "Australia/Perth",
        "Australia/Adelaide",
        "Australia/Darwin",
        "Pacific/Auckland",
        "Pacific/Honolulu",
        "Pacific/Fiji",
        "Africa/Cairo",
        "Africa/Lagos",
        "Africa/Johannesburg",
        "Africa/Nairobi",
        "Africa/Casablanca",
        "Africa/Tunis",
        "Africa/Algiers",
    }

    # For now, accept any properly formatted timezone
    # In a real implementation, you might check against system availability
    return True


def validate_drive_path(drive_path: str) -> bool:
    """Validate storage drive path.

    Args:
        drive_path: Drive path to validate

    Returns:
        True if drive path is valid, False otherwise
    """
    if not drive_path:
        return False

    # Must start with /dev/
    if not drive_path.startswith("/dev/"):
        return False

    # Common drive patterns
    valid_patterns = [
        r"^/dev/sd[a-z]$",  # SATA drives (sda, sdb, etc.)
        r"^/dev/hd[a-z]$",  # IDE drives (hda, hdb, etc.)
        r"^/dev/nvme\d+n\d+$",  # NVMe drives (nvme0n1, nvme1n1, etc.)
        r"^/dev/mmcblk\d+$",  # MMC/SD cards (mmcblk0, mmcblk1, etc.)
        r"^/dev/loop\d+$",  # Loop devices (loop0, loop1, etc.)
        r"^/dev/md\d+$",  # RAID devices (md0, md1, etc.)
        r"^/dev/dm-\d+$",  # Device mapper (dm-0, dm-1, etc.)
    ]

    return any(re.match(pattern, drive_path) for pattern in valid_patterns)


def validate_swap_size(swap_size: str) -> bool:
    """Validate swap size specification.

    Args:
        swap_size: Swap size to validate

    Returns:
        True if swap size is valid, False otherwise
    """
    if not swap_size:
        return False

    # Allow "auto" for automatic calculation
    if swap_size.lower() == "auto":
        return True

    # Validate size with units (e.g., "2G", "512M", "1024K")
    size_pattern = r"^\d+[KMG]?$"

    if not re.match(size_pattern, swap_size.upper()):
        return False

    # Extract numeric value
    if swap_size[-1].upper() in "KMG":
        numeric_part = swap_size[:-1]
        unit = swap_size[-1].upper()
    else:
        numeric_part = swap_size
        unit = "B"

    try:
        size_value = int(numeric_part)
    except ValueError:
        return False

    # Validate reasonable size limits
    if unit == "K":
        min_size, max_size = 1024, 1024 * 1024  # 1K to 1G in KB
    elif unit == "M":
        min_size, max_size = 1, 32 * 1024  # 1M to 32G in MB
    elif unit == "G":
        min_size, max_size = 1, 64  # 1G to 64G in GB
    else:  # Bytes
        min_size, max_size = 1024 * 1024, 64 * 1024 * 1024 * 1024  # 1M to 64G in bytes

    return min_size <= size_value <= max_size
