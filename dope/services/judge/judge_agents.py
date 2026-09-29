"""Pydantic-AI Agents that answer one Jev question each.

Each factory returns a cached ``Agent`` backed by :func:`get_typesafe_model`.
The Agent's ``output_type`` determines the Jev primitive: ``bool`` maps to a
Noul, an ``Enum`` or ``Literal`` of two-plus options maps to a Choice. Bare
``int`` is not supported by the adapter; the doc-priority agent uses a
``Literal[0, 1, 2, 3, 4]`` so Jev picks one of five defined levels. Callers
should fan out concurrently with :func:`asyncio.gather` from
:mod:`dope.services.judge.judge_service`.
"""

from typing import Literal

from pydantic_ai import Agent

from dope.core.classification import ChangeCategory
from dope.core.loop_cache import loop_scoped_cache
from dope.llms.model_factory import get_typesafe_model
from dope.models.enums import ChangeType
from dope.prompts import PromptRegistry


@loop_scoped_cache
def get_change_category_agent() -> Agent[None, ChangeCategory]:
    """Jev Choice over :class:`ChangeCategory`."""
    return Agent(
        model=get_typesafe_model(),
        output_type=ChangeCategory,
        instructions=PromptRegistry.get("judge.change_category").template,
    )


@loop_scoped_cache
def get_change_type_agent() -> Agent[None, ChangeType]:
    """Jev Choice over :class:`ChangeType` (add / change / delete)."""
    return Agent(
        model=get_typesafe_model(),
        output_type=ChangeType,
        instructions=PromptRegistry.get("judge.change_type").template,
    )


@loop_scoped_cache
def get_is_breaking_agent() -> Agent[None, bool]:
    """Jev Noul: does this diff introduce a breaking change?"""
    return Agent(
        model=get_typesafe_model(),
        output_type=bool,
        instructions=PromptRegistry.get("judge.is_breaking").template,
    )


@loop_scoped_cache
def get_is_user_facing_agent() -> Agent[None, bool]:
    """Jev Noul: would a docs-only reader notice this diff?"""
    return Agent(
        model=get_typesafe_model(),
        output_type=bool,
        instructions=PromptRegistry.get("judge.is_user_facing").template,
    )


@loop_scoped_cache
def get_needs_docs_agent() -> Agent[None, bool]:
    """Jev Noul: does this diff warrant a documentation update?"""
    return Agent(
        model=get_typesafe_model(),
        output_type=bool,
        instructions=PromptRegistry.get("judge.needs_docs").template,
    )


@loop_scoped_cache
def get_doc_priority_agent() -> Agent[None, Literal[0, 1, 2, 3, 4]]:
    """Jev Choice over the 0-4 documentation urgency levels.

    A bare ``int`` is not a valid TypeSafe output type; the rubric semantics
    (level meanings) are conveyed through the ``judge.doc_priority`` prompt
    template rather than through per-level schema descriptions.
    """
    return Agent(
        model=get_typesafe_model(),
        output_type=Literal[0, 1, 2, 3, 4],
        instructions=PromptRegistry.get("judge.doc_priority").template,
    )
