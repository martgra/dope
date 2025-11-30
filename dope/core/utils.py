"""Utility functions (legacy - delegates to focused modules).

This module maintains backward compatibility by re-exporting functions
from their new locations. Import from specific modules for new code:

- dope.core.config_locator - Configuration file location
- dope.core.config_io - Configuration I/O operations
- dope.core.project - Project and Git utilities
"""

import sys

# Re-export from new modules for backward compatibility


def require_config():
    """Ensure config exists, exit with helpful message if not.

    Returns:
        Settings: The loaded settings object.

    Raises:
        SystemExit: If no config found.
    """
    from rich import print as rprint

    from dope.core.settings import get_settings

    settings = get_settings()
    if settings.agent is None:
        rprint("[red]❌ No configuration found[/red]")
        rprint("[blue]💡 Run 'dope config init' to set up[/blue]")
        sys.exit(1)
    return settings
