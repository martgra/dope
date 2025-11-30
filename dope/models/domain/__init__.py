"""Domain models for dope application."""

from dope.models.domain.code import CodeChange, CodeChanges
from dope.models.domain.documentation import (
    ChangeSuggestion,
    CodeMetadata,
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

__all__ = [
    # Code models
    "CodeChange",
    "CodeChanges",
    # Documentation models
    "ChangeSuggestion",
    "CodeMetadata",
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
