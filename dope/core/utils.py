"""Core utility functions.

Common helper functions for the dope application.
"""


def require_config():
    """Ensure config exists, exit with helpful message if not.

    Returns:
        Settings: The loaded settings object.

    Raises:
        ConfigurationError: If no config found.
    """
    from dope.exceptions import ConfigurationError
    from dope.models.settings import get_settings

    settings = get_settings()
    if settings.agent is None:
        raise ConfigurationError("No configuration found. Run 'dope config init' to set up.")
    return settings
