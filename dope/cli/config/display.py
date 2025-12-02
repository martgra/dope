"""Configuration display and formatting functions.

DEPRECATED: This module is deprecated. Use dope.cli.ui.formatters.ConfigFormatter instead.
Kept for backwards compatibility.
"""

from dope.cli.ui.formatters import ConfigFormatter
from dope.models.settings import Settings


def display_config_table(settings: Settings) -> None:
    """Display configuration as formatted table.

    DEPRECATED: Use ConfigFormatter.display_table() instead.
    """
    ConfigFormatter.display_table(settings)


def display_config_json(settings: Settings) -> None:
    """Display configuration as JSON.

    DEPRECATED: Use ConfigFormatter.display_json() instead.
    """
    ConfigFormatter.display_json(settings)


def display_config_yaml(settings: Settings) -> None:
    """Display configuration as YAML.

    DEPRECATED: Use ConfigFormatter.display_yaml() instead.
    """
    ConfigFormatter.display_yaml(settings)
