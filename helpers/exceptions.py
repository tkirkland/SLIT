"""Custom exceptions for the SLIT installer.

This module defines all custom exception classes used throughout the installer,
following the error handling framework specified in the utility functions.
"""

from typing import Any, Dict, Optional


class InstallerError(Exception):
    """Base exception class for installer errors.

    Attributes:
        message: Error description
        error_code: Unique error identifier
        context: Error context data
        recoverable: Whether error allows recovery
        user_message: User-friendly error description
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        user_message: Optional[str] = None,
    ) -> None:
        """Initialize InstallerError.

        Args:
            message: Error description
            error_code: Unique error identifier
            context: Error context data
            recoverable: Whether error allows recovery
            user_message: User-friendly error description
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.recoverable = recoverable
        self.user_message = user_message or message


class ValidationError(InstallerError):
    """Configuration validation errors.

    Additional attributes:
        field: Field that failed validation
        invalid_value: The invalid value
        expected_format: Description of expected format
    """

    def __init__(
        self,
        message: str,
        field: str,
        invalid_value: Any,
        expected_format: str,
        **kwargs,
    ) -> None:
        """Initialize ValidationError.

        Args:
            message: Error description
            field: Field that failed validation
            invalid_value: The invalid value
            expected_format: Description of expected format
            **kwargs: Additional InstallerError arguments
        """
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field
        self.invalid_value = invalid_value
        self.expected_format = expected_format


class CommandExecutionError(InstallerError):
    """Command execution errors."""

    def __init__(
        self,
        message: str,
        command: str,
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
        **kwargs,
    ) -> None:
        """Initialize CommandExecutionError.

        Args:
            message: Error description
            command: Command that failed
            exit_code: Process exit code
            stdout: Standard output
            stderr: Standard error
            **kwargs: Additional InstallerError arguments
        """
        super().__init__(message, error_code="COMMAND_EXECUTION_ERROR", **kwargs)
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class HardwareDetectionError(InstallerError):
    """Hardware detection errors."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(message, error_code="HARDWARE_DETECTION_ERROR", **kwargs)


class NetworkConfigurationError(InstallerError):
    """Network configuration errors."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(message, error_code="NETWORK_CONFIGURATION_ERROR", **kwargs)


class SystemRequirementsError(InstallerError):
    """System requirements validation errors."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(message, error_code="SYSTEM_REQUIREMENTS_ERROR", **kwargs)


class InstallationPhaseError(InstallerError):
    """Installation phase execution errors."""

    def __init__(self, message: str, phase_number: int, **kwargs) -> None:
        super().__init__(message, error_code="INSTALLATION_PHASE_ERROR", **kwargs)
        self.phase_number = phase_number
