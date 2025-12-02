"""Logging configuration for dope application.

This module provides a centralized logging setup with human-readable output.
"""

import logging
import os
import sys
from enum import Enum
from typing import TextIO


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Default log format - human readable
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Simple format for CLI output
CLI_FORMAT = "%(levelname)s: %(message)s"


def get_log_level() -> str:
    """Get log level from environment or default to WARNING.

    Environment variable: DOPE_LOG_LEVEL

    Returns:
        Log level string.
    """
    return os.environ.get("DOPE_LOG_LEVEL", "WARNING").upper()


def configure_logging(
    level: str | None = None,
    stream: TextIO | None = None,
    format_string: str = DEFAULT_FORMAT,
) -> None:
    """Configure root logger for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to DOPE_LOG_LEVEL env var or WARNING.
        stream: Output stream. Defaults to stderr.
        format_string: Log format string. Defaults to human-readable format.
    """
    level = level or get_log_level()
    stream = stream or sys.stderr

    # Get numeric level
    numeric_level = getattr(logging, level, logging.WARNING)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        datefmt=DEFAULT_DATE_FORMAT,
        stream=stream,
        force=True,  # Override any existing configuration
    )

    # Set level for dope loggers
    logging.getLogger("dope").setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


# Convenience function for lazy initialization
_initialized = False


def ensure_logging_configured() -> None:
    """Ensure logging is configured (called once)."""
    global _initialized
    if not _initialized:
        configure_logging()
        _initialized = True
