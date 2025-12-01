"""Core utility functions.

Common helper functions for the dope application.
"""

import sys


def require_config():
    """Ensure config exists, exit with helpful message if not.

    Returns:
        Settings: The loaded settings object.

    Raises:
        SystemExit: If no config found.
    """
    from rich import print as rprint

    from dope.models.settings import get_settings

    settings = get_settings()
    if settings.agent is None:
        rprint("[red]❌ No configuration found[/red]")
        rprint("[blue]💡 Run 'dope config init' to set up[/blue]")
        sys.exit(1)
    return settings
