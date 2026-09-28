"""Instructions for TypeSafe (Jev) judgments over a code diff.

Each constant is passed as the ``instructions`` argument of a pydantic-ai
``Agent`` backed by ``TypeSafeModel``. Instructions define the question; the
Agent's ``output_type`` defines the answer shape (Noul, Choice, or Score).
"""

CHANGE_CATEGORY_INSTRUCTIONS = (
    "Given a git diff, pick the single category that best describes what the "
    "change is about. Judge by the intent of the change, not by the file path."
)

CHANGE_TYPE_INSTRUCTIONS = (
    "Given a git diff, decide whether it primarily adds new behavior, modifies "
    "existing behavior, or removes behavior. Focus on the net effect for a "
    "consumer of the code, not on line counts."
)

IS_BREAKING_INSTRUCTIONS = (
    "Given a git diff, answer true if it introduces a breaking change for "
    "someone depending on this code (removed or renamed public API, changed "
    "signature or return type, changed behavior contract, config or migration "
    "required). Answer false for internal refactors, tests, and additions."
)

IS_USER_FACING_INSTRUCTIONS = (
    "Given a git diff, answer true if a user reading only the documentation "
    "would notice this change. Public CLI, API, configuration, error "
    "messages, and observable behavior count as user-facing. Internal "
    "refactors, tests, tooling, and comments do not."
)

NEEDS_DOCS_INSTRUCTIONS = (
    "Given a git diff, answer true if the documentation should be updated to "
    "reflect it. Consider whether existing docs would become misleading, "
    "incomplete, or outdated if this change shipped without a doc update."
)

DOC_PRIORITY_INSTRUCTIONS = (
    "Given a git diff, rate how urgent it is to update documentation on a "
    "0-4 scale:\n"
    "  0 - No doc update needed (internal, invisible, or fully covered).\n"
    "  1 - Nice to have; existing docs remain accurate.\n"
    "  2 - Should be documented; small addition or clarification.\n"
    "  3 - Important; users will look for information about this change.\n"
    "  4 - Critical; leaving docs unchanged is misleading or breaks users."
)
