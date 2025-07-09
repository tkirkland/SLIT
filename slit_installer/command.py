"""Command execution system for the SLIT installer.

This module provides central command execution with logging, dry-run support,
and comprehensive error handling as specified in the utility functions.
"""

import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from .exceptions import CommandExecutionError
from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class CommandResult:
    """Result of command execution.

    Attributes:
        success: Whether command succeeded
        exit_code: Process exit code
        stdout: Standard output
        stderr: Standard error
        duration: Execution time in seconds
    """

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float


class CommandExecutor:
    """Central command execution system."""

    def __init__(self, dry_run: bool = False) -> None:
        """Initialize CommandExecutor.

        Args:
            dry_run: If True, simulate command execution
        """
        self.dry_run = dry_run

    @staticmethod
    def _prepare_command(command: Union[str, List[str]]) -> List[str]:
        """Convert command to list format.

        Args:
            command: Command as string or list

        Returns:
            Command as list of strings
        """
        if isinstance(command, str):
            return command.split()
        return command

    @staticmethod
    def _prepare_subprocess_args(
        cmd_list: List[str],
        capture_output: bool,
        timeout: Optional[int],
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        input_data: Optional[str],
    ) -> Dict[str, Any]:
        """Prepare subprocess arguments.

        Args:
            cmd_list: Command as list of strings
            capture_output: Whether to capture output
            timeout: Command timeout
            cwd: Working directory
            env: Environment variables
            input_data: Input data for stdin

        Returns:
            Dictionary of subprocess arguments
        """
        return {
            "args": cmd_list,
            "capture_output": capture_output,
            "text": True,
            "timeout": timeout,
            "cwd": cwd,
            "env": env,
            "input": input_data,
        }

    @staticmethod
    def _handle_dry_run(cmd_list: List[str]) -> CommandResult:
        """Handle dry run execution.

        Args:
            cmd_list: Command as list of strings

        Returns:
            CommandResult for dry run
        """
        logger.info(f"DRY RUN: Would execute: {' '.join(cmd_list)}")
        return CommandResult(
            success=True,
            exit_code=0,
            stdout="[DRY RUN] Command would execute successfully",
            stderr="",
            duration=0.0,
        )

    @staticmethod
    def _create_result(
        subprocess_result: subprocess.CompletedProcess, duration: float
    ) -> CommandResult:
        """Create CommandResult from subprocess result.

        Args:
            subprocess_result: Completed subprocess result
            duration: Execution duration in seconds

        Returns:
            CommandResult object
        """
        success = subprocess_result.returncode == 0
        return CommandResult(
            success=success,
            exit_code=subprocess_result.returncode,
            stdout=subprocess_result.stdout or "",
            stderr=subprocess_result.stderr or "",
            duration=duration,
        )

    @staticmethod
    def _log_result(result: CommandResult, description: str) -> None:
        """Log command execution result.

        Args:
            result: Command execution result
            description: Command description
        """
        if result.success:
            logger.info(f"'{description}' succeeded in {result.duration:.2f}s")
        else:
            logger.error(f"'{description}' failed with exit code {result.exit_code}")
            if result.stderr:
                logger.error(f"Error output: {result.stderr}")

    @staticmethod
    def _handle_timeout_error(
        e: subprocess.TimeoutExpired,
        cmd_list: List[str],
        description: str,
        timeout: int,
        duration: float,
        check_success: bool,
    ) -> CommandResult:
        """Handle timeout errors.

        Args:
            e: Timeout exception
            cmd_list: Command as list of strings
            description: Command description
            timeout: Timeout value
            duration: Execution duration
            check_success: Whether to raise on error

        Returns:
            CommandResult object

        Raises:
            CommandExecutionError: If check_success is True
        """
        logger.error(f"Command timed out after {timeout}s")

        if check_success:
            raise CommandExecutionError(
                f"Command timed out: {description}",
                command=" ".join(cmd_list),
                exit_code=-1,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
            )

        return CommandResult(
            success=False,
            exit_code=-1,
            stdout=e.stdout or "",
            stderr=e.stderr or "",
            duration=duration,
        )

    @staticmethod
    def _handle_general_error(
        e: Exception,
        cmd_list: List[str],
        description: str,
        duration: float,
        check_success: bool,
    ) -> CommandResult:
        """Handle general execution errors.

        Args:
            e: Exception that occurred
            cmd_list: Command as list of strings
            description: Command description
            duration: Execution duration
            check_success: Whether to raise on error

        Returns:
            CommandResult object

        Raises:
            CommandExecutionError: If check_success is True
        """
        logger.error(f"Command execution error: {e}")

        if check_success:
            raise CommandExecutionError(
                f"Command execution failed: {description}",
                command=" ".join(cmd_list),
                exit_code=-1,
                stdout="",
                stderr=str(e),
            )

        return CommandResult(
            success=False, exit_code=-1, stdout="", stderr=str(e), duration=duration
        )

    def execute_command(
        self,
        command: Union[str, List[str]],
        description: str,
        capture_output: bool = True,
        check_success: bool = True,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[str] = None,
    ) -> CommandResult:
        """Execute system command with comprehensive logging and error handling.

        Args:
            command: System command to execute
            description: Human-readable description for UI/logging
            capture_output: Return command output
            check_success: Raise error on non-zero exit
            timeout: Command timeout in seconds
            cwd: Working directory
            env: Environment variables
            input_data: Data to send to stdin

        Returns:
            CommandResult object with execution details

        Raises:
            CommandExecutionError: On command failure if check_success=True
        """
        start_time = time.time()
        cmd_list = self._prepare_command(command)

        logger.info(f"Executing: {description}")
        logger.debug(f"Command: {' '.join(cmd_list)}")

        if self.dry_run:
            return self._handle_dry_run(cmd_list)

        try:
            subprocess_args = self._prepare_subprocess_args(
                cmd_list, capture_output, timeout, cwd, env, input_data
            )

            result = subprocess.run(**subprocess_args)
            duration = time.time() - start_time

            cmd_result = self._create_result(result, duration)
            self._log_result(cmd_result, description)

            # Check for errors if requested
            if check_success and not cmd_result.success:
                raise CommandExecutionError(
                    f"Command failed: {description}",
                    command=" ".join(cmd_list),
                    exit_code=result.returncode,
                    stdout=result.stdout or "",
                    stderr=result.stderr or "",
                )

            return cmd_result

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return self._handle_timeout_error(
                e, cmd_list, description, timeout, duration, check_success
            )

        except Exception as e:
            duration = time.time() - start_time
            return self._handle_general_error(
                e, cmd_list, description, duration, check_success
            )

    def execute_command_with_progress(
        self,
        command: Union[str, List[str]],
        description: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        **kwargs,
    ) -> CommandResult:
        """Execute command with real-time progress reporting.

        Args:
            command: System command to execute
            description: Human-readable description
            progress_callback: Called with progress updates
            **kwargs: Additional arguments for execute_command

        Returns:
            CommandResult object
        """
        if progress_callback:
            progress_callback(0, 1, f"Starting: {description}")

        try:
            result = self.execute_command(command, description, **kwargs)

            if progress_callback:
                progress_callback(1, 1, f"Completed: {description}")

            return result

        except Exception as _:
            if progress_callback:
                progress_callback(0, 1, f"Failed: {description}")
            raise


# Global command executor instance
_command_executor: Optional[CommandExecutor] = None
blowfish_key: Optional[str] = None


def get_command_executor() -> CommandExecutor:
    """Get a global command executor instance.

    Returns:
        CommandExecutor instance
    """
    global _command_executor
    if _command_executor is None:
        _command_executor = CommandExecutor()
    return _command_executor


def set_dry_run_mode(dry_run: bool) -> None:
    """Set global dry run mode.

    Args:
        dry_run: Enable/disable dry run mode
    """
    global _command_executor
    _command_executor = CommandExecutor(dry_run=dry_run)


def execute_command(
    command: Union[str, List[str]], description: str, **kwargs
) -> CommandResult:
    """Execute command using global executor.

    Args:
        command: System command to execute
        description: Human-readable description
        **kwargs: Additional arguments for CommandExecutor.execute_command

    Returns:
        CommandResult object
    """
    return get_command_executor().execute_command(command, description, **kwargs)


def execute_command_with_progress(
    command: Union[str, List[str]],
    description: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    **kwargs,
) -> CommandResult:
    """Execute command with progress reporting using global executor.

    Args:
        command: System command to execute
        description: Human-readable description
        progress_callback: Progress callback function
        **kwargs: Additional arguments for CommandExecutor.execute_command

    Returns:
        CommandResult object
    """
    return get_command_executor().execute_command_with_progress(
        command, description, progress_callback, **kwargs
    )
