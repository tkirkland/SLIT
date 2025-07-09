"""Logging system for the SLIT installer.

This module provides comprehensive logging functionality with timestamped entries,
automatic log rotation, and multi-level filtering as specified in the utility functions.
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Default log directory
DEFAULT_LOG_DIR = Path("logs")

# Global logger configuration
_logger_initialized = False
_log_handlers: Dict[str, logging.Handler] = {}


def initialize_logging(
    log_file: Optional[str] = None,
    level: str = "INFO",
    console_output: bool = True,
    log_dir: Optional[str] = None,
) -> None:
    """Set up comprehensive logging system.

    Args:
        log_file: Path to log file (auto-generated if None)
        level: Logging level (DEBUG, INFO, WARN, ERROR)
        console_output: Enable console logging
        log_dir: Directory for log files
    """
    global _logger_initialized, _log_handlers

    if _logger_initialized:
        return

    # Create log directory
    if log_dir:
        log_directory = Path(log_dir)
    else:
        log_directory = DEFAULT_LOG_DIR

    log_directory.mkdir(exist_ok=True)

    # Generate log filename if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_directory / f"slit-install-{timestamp}.log"
    else:
        log_file = Path(log_file)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    _log_handlers["file"] = file_handler

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        _log_handlers["console"] = console_handler

    # Clean up old logs
    cleanup_old_logs(log_directory)

    _logger_initialized = True

    # Log initialization
    logger = get_logger(__name__)
    logger.info(f"Logging initialized - Level: {level}, File: {log_file}")


def cleanup_old_logs(log_dir: Path, max_age_days: int = 30) -> None:
    """Clean up old log files.

    Args:
        log_dir: Directory containing log files
        max_age_days: Maximum age of log files in days
    """
    if not log_dir.exists():
        return

    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

    for log_file in log_dir.glob("slit-install-*.log"):
        try:
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                print(f"Removed old log file: {log_file}")
        except OSError:
            # Ignore errors removing old logs
            pass


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if not _logger_initialized:
        initialize_logging()

    return logging.getLogger(name)


def log(level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Write structured log entry.

    Args:
        level: Log level (DEBUG, INFO, WARN, ERROR)
        message: Log message
        context: Additional context data
    """
    logger = get_logger("slit_installer")

    # Format message with context
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        formatted_message = f"{message} | {context_str}"
    else:
        formatted_message = message

    # Log at appropriate level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, formatted_message)


def log_debug(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log debug message.

    Args:
        message: Debug message
        context: Additional context data
    """
    log("DEBUG", message, context)


def log_info(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log info message.

    Args:
        message: Info message
        context: Additional context data
    """
    log("INFO", message, context)


def log_warning(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log warning message.

    Args:
        message: Warning message
        context: Additional context data
    """
    log("WARN", message, context)


def log_error(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log error message.

    Args:
        message: Error message
        context: Additional context data
    """
    log("ERROR", message, context)


def set_log_level(level: str) -> None:
    """Set logging level for all handlers.

    Args:
        level: New logging level (DEBUG, INFO, WARN, ERROR)
    """
    log_level = getattr(logging, level.upper())

    # Update root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Update console handler if exists
    if "console" in _log_handlers:
        _log_handlers["console"].setLevel(log_level)


def get_log_file_path() -> Optional[Path]:
    """Get current log file path.

    Returns:
        Path to current log file or None if not initialized
    """
    if "file" not in _log_handlers:
        return None

    file_handler = _log_handlers["file"]
    if hasattr(file_handler, "baseFilename"):
        return Path(file_handler.baseFilename)

    return None


class LogContext:
    """Context manager for adding context to all log messages."""

    def __init__(self, context: Dict[str, Any]) -> None:
        """Initialize LogContext.

        Args:
            context: Context to add to log messages
        """
        self.context = context
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self) -> "LogContext":
        """Enter context manager."""

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            # Add context to record
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        logging.setLogRecordFactory(self.old_factory)
