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
        
    def execute_command(
        self,
        command: Union[str, List[str]],
        description: str,
        capture_output: bool = True,
        check_success: bool = True,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[str] = None
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
        
        # Convert command to list if string
        if isinstance(command, str):
            cmd_list = command.split()
        else:
            cmd_list = command
        
        logger.info(f"Executing: {description}")
        logger.debug(f"Command: {' '.join(cmd_list)}")
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would execute: {' '.join(cmd_list)}")
            return CommandResult(
                success=True,
                exit_code=0,
                stdout="[DRY RUN] Command would execute successfully",
                stderr="",
                duration=0.0
            )
        
        try:
            # Prepare subprocess arguments
            subprocess_args = {
                'args': cmd_list,
                'capture_output': capture_output,
                'text': True,
                'timeout': timeout,
                'cwd': cwd,
                'env': env,
                'input': input_data
            }
            
            # Execute command
            result = subprocess.run(**subprocess_args)
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            # Log result
            if success:
                logger.info(f"Command succeeded in {duration:.2f}s")
            else:
                logger.error(f"Command failed with exit code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr}")
            
            # Create result object
            cmd_result = CommandResult(
                success=success,
                exit_code=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                duration=duration
            )
            
            # Check for errors if requested
            if check_success and not success:
                raise CommandExecutionError(
                    f"Command failed: {description}",
                    command=' '.join(cmd_list),
                    exit_code=result.returncode,
                    stdout=result.stdout or "",
                    stderr=result.stderr or ""
                )
            
            return cmd_result
            
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            logger.error(f"Command timed out after {timeout}s")
            
            if check_success:
                raise CommandExecutionError(
                    f"Command timed out: {description}",
                    command=' '.join(cmd_list),
                    exit_code=-1,
                    stdout=e.stdout or "",
                    stderr=e.stderr or ""
                )
            
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Command execution error: {e}")
            
            if check_success:
                raise CommandExecutionError(
                    f"Command execution failed: {description}",
                    command=' '.join(cmd_list),
                    exit_code=-1,
                    stdout="",
                    stderr=str(e)
                )
            
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=duration
            )
    
    def execute_command_with_progress(
        self,
        command: Union[str, List[str]],
        description: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        **kwargs
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
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, 1, f"Failed: {description}")
            raise


# Global command executor instance
_command_executor: Optional[CommandExecutor] = None


def get_command_executor() -> CommandExecutor:
    """Get global command executor instance.
    
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
    command: Union[str, List[str]],
    description: str,
    **kwargs
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
    **kwargs
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