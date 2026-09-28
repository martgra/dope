"""Domain models for dope application."""

from dope.models.domain.code import CodeChange, CodeChanges, CodeMetadata
from dope.models.domain.documentation import (
    ChangeSuggestion,
    DocSection,
    DocSuggestions,
    DocSummary,
    SuggestedChange,
)
from dope.models.domain.judgment import DiffJudgment
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
    "AlignedScope",
    "ChangeSuggestion",
    "ChangeType",
    "CodeChange",
    "CodeChanges",
    "CodeMetadata",
    "DiffJudgment",
    "DocSection",
    "DocSectionTemplate",
    "DocSuggestions",
    "DocSummary",
    "DocTemplate",
    "ScopeSuggestedChange",
    "ScopeTemplate",
    "StructureTemplate",
    "SuggestedChange",
]
