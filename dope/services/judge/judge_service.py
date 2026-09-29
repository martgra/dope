"""Assemble a DiffJudgment by running six TypeSafe (Jev) Agents in parallel."""

import asyncio
import logging

from dope.core.usage import UsageTracker
from dope.llms.usage_limits import DEFAULT_USAGE_LIMITS
from dope.models.domain.judgment import DiffJudgment
from dope.services.judge.judge_agents import (
    get_align_minimality_agent,
    get_change_category_agent,
    get_change_type_agent,
    get_doc_priority_agent,
    get_is_breaking_agent,
    get_is_user_facing_agent,
    get_needs_docs_agent,
)

logger = logging.getLogger(__name__)


async def judge_diff(
    diff: str,
    usage_tracker: UsageTracker | None = None,
) -> DiffJudgment:
    """Produce a structured Jev judgment for a single code diff.

    Six pydantic-ai Agents backed by ``TypeSafeModel`` run concurrently via
    :func:`asyncio.gather`, each answering one narrow question. Their typed
    outputs are assembled into a :class:`DiffJudgment`.

    Args:
        diff: Raw git diff passed verbatim as the user prompt to each agent.
            Keep it to a reasonable size for the token budget.
        usage_tracker: Optional tracker whose ``usage`` field is forwarded to
            each agent's ``run`` call for token accounting.

    Returns:
        A :class:`DiffJudgment` with all six fields populated.
    """
    usage = usage_tracker.usage if usage_tracker else None
    limits = DEFAULT_USAGE_LIMITS
    (
        category_r,
        change_type_r,
        is_breaking_r,
        is_user_facing_r,
        needs_docs_r,
        priority_r,
    ) = await asyncio.gather(
        get_change_category_agent().run(user_prompt=diff, usage=usage, usage_limits=limits),
        get_change_type_agent().run(user_prompt=diff, usage=usage, usage_limits=limits),
        get_is_breaking_agent().run(user_prompt=diff, usage=usage, usage_limits=limits),
        get_is_user_facing_agent().run(user_prompt=diff, usage=usage, usage_limits=limits),
        get_needs_docs_agent().run(user_prompt=diff, usage=usage, usage_limits=limits),
        get_doc_priority_agent().run(user_prompt=diff, usage=usage, usage_limits=limits),
    )
    return DiffJudgment(
        change_category=category_r.output,
        change_type=change_type_r.output,
        is_breaking=is_breaking_r.output,
        is_user_facing=is_user_facing_r.output,
        needs_docs=needs_docs_r.output,
        doc_priority=priority_r.output,
    )


async def judge_alignment_preserves_scope(
    scope: str,
    original_content: str,
    aligned_content: str,
    usage_tracker: UsageTracker | None = None,
) -> bool:
    """Ask Jev whether the aligner's rewrite is minimal versus the scope.

    Returns ``True`` when the rewrite only touches scope-required content
    (safe to write), ``False`` when the aligner over-rewrote and the caller
    should keep the original file. When the two contents are byte-identical
    the gate short-circuits to ``True`` and does not spend a Jev call.

    Args:
        scope: The scope requirements for this file, as fed to the aligner.
        original_content: File content before the aligner ran.
        aligned_content: File content the aligner returned.
        usage_tracker: Optional tracker for token accounting.

    Returns:
        True if the rewrite is minimal, False if it over-rewrote.
    """
    if original_content == aligned_content:
        return True
    if not original_content.strip():
        # Pure creation — there is nothing to preserve, so any output is
        # trivially "minimal versus the (nonexistent) original".
        return True
    user_prompt = (
        "<scope>\n"
        f"{scope}\n"
        "</scope>\n\n"
        "<original_content>\n"
        f"{original_content}\n"
        "</original_content>\n\n"
        "<aligned_content>\n"
        f"{aligned_content}\n"
        "</aligned_content>"
    )
    usage = usage_tracker.usage if usage_tracker else None
    result = await get_align_minimality_agent().run(
        user_prompt=user_prompt,
        usage=usage,
        usage_limits=DEFAULT_USAGE_LIMITS,
    )
    return bool(result.output)
