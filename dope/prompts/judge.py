"""Registered prompts (instructions) for the six TypeSafe Jev judge agents."""

from __future__ import annotations

from dope.prompts import Prompt, PromptRegistry

PromptRegistry.register(
    Prompt(
        name="judge.change_category",
        version="v1",
        description="Jev Choice: what ChangeCategory does this diff belong to?",
        template=(
            "Given a git diff, pick the single category that best describes what the "
            "change is about. Judge by the intent of the change, not by the file path."
        ),
    )
)

PromptRegistry.register(
    Prompt(
        name="judge.change_type",
        version="v1",
        description="Jev Choice: does the diff add / modify / delete behavior?",
        template=(
            "Given a git diff, decide whether it primarily adds new behavior, modifies "
            "existing behavior, or removes behavior. Focus on the net effect for a "
            "consumer of the code, not on line counts."
        ),
    )
)

PromptRegistry.register(
    Prompt(
        name="judge.is_breaking",
        version="v1",
        description="Jev Noul: does the diff break something users depend on?",
        template=(
            "Given a git diff, answer true if it introduces a breaking change for "
            "someone depending on this code (removed or renamed public API, changed "
            "signature or return type, changed behavior contract, config or migration "
            "required). Answer false for internal refactors, tests, and additions."
        ),
    )
)

PromptRegistry.register(
    Prompt(
        name="judge.is_user_facing",
        version="v1",
        description="Jev Noul: would a docs-only reader notice this change?",
        template=(
            "Given a git diff, answer true if a user reading only the documentation "
            "would notice this change. Public CLI, API, configuration, error "
            "messages, and observable behavior count as user-facing. Internal "
            "refactors, tests, tooling, and comments do not."
        ),
    )
)

PromptRegistry.register(
    Prompt(
        name="judge.needs_docs",
        version="v1",
        description="Jev Noul: does the diff warrant a documentation update?",
        template=(
            "Given a git diff, answer true if the documentation should be updated to "
            "reflect it. Consider whether existing docs would become misleading, "
            "incomplete, or outdated if this change shipped without a doc update."
        ),
    )
)

PromptRegistry.register(
    Prompt(
        name="judge.doc_priority",
        version="v1",
        description="Jev Choice over 0-4: documentation urgency rubric.",
        template=(
            "Given a git diff, rate how urgent it is to update documentation on a "
            "0-4 scale:\n"
            "  0 - No doc update needed (internal, invisible, or fully covered).\n"
            "  1 - Nice to have; existing docs remain accurate.\n"
            "  2 - Should be documented; small addition or clarification.\n"
            "  3 - Important; users will look for information about this change.\n"
            "  4 - Critical; leaving docs unchanged is misleading or breaks users."
        ),
    )
)

PromptRegistry.register(
    Prompt(
        name="judge.align_preserves_scope",
        version="v1",
        description=(
            "Jev Noul post-aligner gate: does the aligned rewrite change only "
            "content the scope requires, preserving everything else? Answer "
            "true when the rewrite is minimal (only scope-required lines "
            "touched), false when the aligner over-rewrote (rephrased, "
            "reordered, or stylistically edited content the scope does not "
            "require to change). Ground the judgment in the ``scope`` "
            "requirements versus the diff between ``original_content`` and "
            "``aligned_content``. Additions the scope requires and deletions "
            "of content the scope moves elsewhere are fine; wording changes "
            "on untouched-by-scope sections are not."
        ),
        template=(
            "You are the minimality gate for a doc-alignment pipeline. Given "
            "the scope requirements for a file, the original content, and "
            "the aligner's rewrite, answer whether the rewrite preserves "
            "everything the scope does not explicitly require to change.\n"
            "\n"
            "Answer TRUE when the rewrite is minimal: additions match "
            "scope-required sections, deletions match content the scope "
            "moves elsewhere, and every other line is byte-identical to the "
            "original (or trivially reformatted whitespace).\n"
            "\n"
            "Answer FALSE when the aligner over-rewrote: rephrased fine "
            "sentences, reordered untouched lines, changed heading casing, "
            "modernized command syntax, expanded terse sections beyond what "
            "the scope calls for, or otherwise touched content the scope "
            "does not require."
        ),
    )
)

PromptRegistry.register(
    Prompt(
        name="judge.align_preserves_scope",
        version="v2-move-aware",
        description=(
            "Move-aware variant of the post-aligner gate. The v1 prompt "
            "false-rejected legitimate cross-file moves: if the aligner "
            "correctly removed out-of-scope content and emitted a "
            "``changes_in_other_files`` entry to relocate it, v1 saw the "
            "large deletion as an over-rewrite. v2 receives the aligner's "
            "``moves`` list explicitly and instructs Jev to treat "
            "deletions whose content shows up in a move as legitimate."
        ),
        template=(
            "You are the minimality gate for a doc-alignment pipeline. You "
            "receive four things: the scope requirements for a file, the "
            "original content, the aligner's rewrite, and the aligner's "
            "list of MOVES (cross-file relocations it also asked for). "
            "Answer whether the rewrite preserves everything the scope "
            "does not explicitly require to change.\n"
            "\n"
            "Answer TRUE when the rewrite is minimal:\n"
            "  - Additions match scope-required sections.\n"
            "  - Deletions match either content the scope moves elsewhere OR "
            "content that appears in a MOVE entry — the aligner is allowed "
            "to remove text from this file when it has already routed that "
            "text to another file via a move.\n"
            "  - Every other line is byte-identical to the original (or "
            "trivially reformatted whitespace).\n"
            "\n"
            "Answer FALSE when the aligner over-rewrote:\n"
            "  - Rephrased fine sentences that neither the scope nor a "
            "move required to change.\n"
            "  - Reordered untouched lines.\n"
            "  - Changed heading casing, modernized command syntax, or "
            "expanded terse sections beyond what the scope calls for.\n"
            "  - Deleted content that is neither out-of-scope for this file "
            "nor accounted for by a move."
        ),
    )
)
