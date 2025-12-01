"""Pydantic models for dope application.

This module provides all data models used throughout the application,
organized into logical groups for easy importing.
"""

# Settings models
# Constants
from dope.models.constants import (
    APP_NAME,
    CONFIG_FILENAME,
    DEFAULT_BRANCH,
    DEFAULT_DOC_SUFFIX,
    DESCRIBE_CODE_STATE_FILENAME,
    DESCRIBE_DOCS_STATE_FILENAME,
    DOC_SUFFIX,
    EXCLUDE_DIRS,
    LOCAL_CACHE_FOLDER,
    SUGGESTION_STATE_FILENAME,
)

# Domain models - Code
from dope.models.domain.code import CodeChange, CodeChanges, CodeMetadata

# Domain models - Documentation
from dope.models.domain.documentation import (
    ChangeSuggestion,
    DocSection,
    DocSuggestions,
    DocSummary,
    SuggestedChange,
)

# Domain models - Scope
from dope.models.domain.scope import (
    AlignedScope,
    DocSectionTemplate,
    DocTemplate,
    ScopeTemplate,
    StructureTemplate,
)
from dope.models.domain.scope import (
    SuggestedChange as ScopeSuggestedChange,
)

# Enums
from dope.models.enums import (
    ChangeType,
    DocTemplateKey,
    ProjectTier,
    Provider,
    SectionAudience,
    SectionTheme,
)
from dope.models.settings import (
    AgentSettings,
    CodeRepoSettings,
    DocSettings,
    Settings,
    get_settings,
)

# Shared types
from dope.models.shared import FileSuffix

__all__ = [
    # Settings
    "AgentSettings",
    "CodeRepoSettings",
    "DocSettings",
    "Settings",
    "get_settings",
    # Shared
    "FileSuffix",
    # Enums
    "ChangeType",
    "DocTemplateKey",
    "ProjectTier",
    "Provider",
    "SectionAudience",
    "SectionTheme",
    # Domain - Code
    "CodeChange",
    "CodeChanges",
    # Domain - Documentation
    "ChangeSuggestion",
    "CodeMetadata",
    "DocSection",
    "DocSuggestions",
    "DocSummary",
    "SuggestedChange",
    # Domain - Scope
    "AlignedScope",
    "DocSectionTemplate",
    "DocTemplate",
    "ScopeTemplate",
    "ScopeSuggestedChange",
    "StructureTemplate",
    # Constants
    "APP_NAME",
    "CONFIG_FILENAME",
    "DEFAULT_BRANCH",
    "DEFAULT_DOC_SUFFIX",
    "DESCRIBE_CODE_STATE_FILENAME",
    "DESCRIBE_DOCS_STATE_FILENAME",
    "DOC_SUFFIX",
    "EXCLUDE_DIRS",
    "LOCAL_CACHE_FOLDER",
    "SUGGESTION_STATE_FILENAME",
]
