"""Settings module - backward compatibility wrapper.

DEPRECATED: Import from dope.models.settings instead.
This module provides backward compatibility and will remain for the foreseeable future.
"""

# Import from new location for backward compatibility
from dope.models.settings import (
    AgentSettings,
    CodeRepoSettings,
    DocSettings,
    Settings,
    get_settings,
)

__all__ = [
    "AgentSettings",
    "CodeRepoSettings",
    "DocSettings",
    "Settings",
    "get_settings",
]
