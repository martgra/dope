"""Tests for the logging module."""

import io
import logging

import pytest

from dope.core.logging import (
    CLI_FORMAT,
    DEFAULT_FORMAT,
    configure_logging,
    ensure_logging_configured,
    get_log_level,
    get_logger,
)


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    # Clear all handlers from dope loggers
    for name in ["dope", "dope.services", "dope.cli", "dope.core"]:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    # Reset the module's initialization flag
    import dope.core.logging as log_module

    log_module._initialized = False

    yield


class TestGetLogLevel:
    """Tests for get_log_level function."""

    def test_default_level_is_warning(self, monkeypatch):
        """Test default log level is WARNING."""
        monkeypatch.delenv("DOPE_LOG_LEVEL", raising=False)
        assert get_log_level() == "WARNING"

    def test_respects_environment_variable(self, monkeypatch):
        """Test log level from environment variable."""
        monkeypatch.setenv("DOPE_LOG_LEVEL", "DEBUG")
        assert get_log_level() == "DEBUG"

    def test_uppercases_level(self, monkeypatch):
        """Test log level is uppercased."""
        monkeypatch.setenv("DOPE_LOG_LEVEL", "debug")
        assert get_log_level() == "DEBUG"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configures_with_default_level(self, monkeypatch):
        """Test configure_logging uses default level."""
        monkeypatch.delenv("DOPE_LOG_LEVEL", raising=False)
        stream = io.StringIO()

        configure_logging(stream=stream)

        # Verify dope logger is configured
        logger = logging.getLogger("dope")
        assert logger.level == logging.WARNING

    def test_configures_with_custom_level(self):
        """Test configure_logging with custom level."""
        stream = io.StringIO()

        configure_logging(level="DEBUG", stream=stream)

        logger = logging.getLogger("dope")
        assert logger.level == logging.DEBUG

    def test_configures_with_custom_format(self):
        """Test configure_logging with custom format."""
        stream = io.StringIO()

        configure_logging(level="INFO", stream=stream, format_string=CLI_FORMAT)

        logger = logging.getLogger("dope.test")
        logger.info("Test message")

        output = stream.getvalue()
        assert "INFO: Test message" in output


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger_with_name(self):
        """Test get_logger returns logger with correct name."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"

    def test_returns_same_logger_for_same_name(self):
        """Test get_logger returns same instance for same name."""
        logger1 = get_logger("test.module")
        logger2 = get_logger("test.module")
        assert logger1 is logger2


class TestEnsureLoggingConfigured:
    """Tests for ensure_logging_configured function."""

    def test_configures_only_once(self, monkeypatch):
        """Test ensure_logging_configured only runs once."""
        import dope.core.logging as log_module

        monkeypatch.delenv("DOPE_LOG_LEVEL", raising=False)

        assert log_module._initialized is False

        ensure_logging_configured()
        assert log_module._initialized is True

        # Second call should not reconfigure
        ensure_logging_configured()
        assert log_module._initialized is True
