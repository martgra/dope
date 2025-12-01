"""Domain models for dope application."""

from dope.models.domain.code import CodeChange, CodeChanges, CodeMetadata
from dope.models.domain.documentation import (
    ChangeSuggestion,
    DocSection,
    DocSuggestions,
    DocSummary,
    SuggestedChange,
)
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
from dope.models.enums import ChangeType

__all__ = [
    # Code models
    "CodeChange",
    "CodeChanges",
    "CodeMetadata",
    # Documentation models
    "ChangeSuggestion",
    "ChangeType",
    "DocSection",
    "DocSuggestions",
    "DocSummary",
    "SuggestedChange",
    # Scope models
    "AlignedScope",
    "DocSectionTemplate",
    "DocTemplate",
    "ScopeTemplate",
    "ScopeSuggestedChange",
    "StructureTemplate",
]
