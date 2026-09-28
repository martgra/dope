"""Domain models for TypeSafe (Jev) judgments over code changes."""

from pydantic import BaseModel, Field

from dope.core.classification import ChangeCategory
from dope.models.enums import ChangeType


class DiffJudgment(BaseModel):
    """Structured judgments about a single code diff.

    Produced by :mod:`dope.services.judge` using Jev via pydantic-ai. Each field
    is a typed answer to one narrow question over the same diff, so downstream
    filtering and prioritization can act on calibrated signals instead of the
    path-based heuristics in :mod:`dope.core.classification`.

    Attributes:
        change_category: Semantic category of the change (e.g. feature, bugfix).
        change_type: Whether the change adds, modifies, or deletes behavior.
        is_breaking: True if the change breaks something users depend on.
        is_user_facing: True if a docs-only reader would notice this change.
        needs_docs: True if the change warrants any doc update at all.
        doc_priority: Ordinal 0-4 rubric score for documentation urgency.
    """

    change_category: ChangeCategory = Field(..., description="Semantic categorization of the diff.")
    change_type: ChangeType = Field(
        ..., description="Whether the change adds, modifies, or deletes behavior."
    )
    is_breaking: bool = Field(
        ..., description="True if the change breaks something users depend on."
    )
    is_user_facing: bool = Field(
        ..., description="True if the change is visible to users through docs."
    )
    needs_docs: bool = Field(
        ..., description="True if the change warrants any documentation update."
    )
    doc_priority: int = Field(..., ge=0, le=4, description="Documentation urgency on a 0-4 rubric.")
