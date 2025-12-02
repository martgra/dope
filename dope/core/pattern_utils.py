"""Utilities for normalizing and merging code path patterns.

Provides language-agnostic pattern generation from concrete file paths
and pattern deduplication for scope-based filtering.
"""

import re
from pathlib import Path


def normalize_code_path(file_path: str) -> list[str]:
    """Generate glob pattern variants from a concrete file path.

    Creates multiple levels of generalization to match similar files:
    - Component-level: Matches any file in same component (e.g., */cli/*)
    - Deep component: Matches nested paths (e.g., **/cli/**)
    - Rooted pattern: Maintains path structure (e.g., dope/cli/*)

    Args:
        file_path: Concrete file path (e.g., "dope/cli/main.py")

    Returns:
        List of glob patterns in order of specificity (most specific first)

    Example:
        >>> normalize_code_path("dope/cli/main.py")
        ['dope/cli/*', '*/cli/*', '**/cli/**']
        >>> normalize_code_path("src/api/routes/users.py")
        ['src/api/routes/*', '*/routes/*', '**/routes/**', 'src/api/*', '*/api/*', '**/api/**']
    """
    if not file_path:
        return []

    patterns: list[str] = []
    path = Path(file_path)

    # Get path components (exclude filename)
    parts = list(path.parent.parts) if path.parent != Path(".") else []

    if not parts:
        return []

    # Skip common noise directories
    noise_parts = {"__pycache__", "node_modules", ".git", "dist", "build"}

    # Generate patterns for each meaningful component
    for i in range(len(parts) - 1, -1, -1):
        part = parts[i]

        # Skip noise
        if part in noise_parts:
            continue

        # Rooted pattern: maintains path structure from root
        if i == 0:
            rooted = "/".join(parts[: i + 1]) + "/*"
            patterns.append(rooted)

        # Component-level pattern: matches in any parent directory
        component = f"*/{part}/*"
        patterns.append(component)

        # Deep component pattern: matches at any nesting level
        deep = f"**/{part}/**"
        patterns.append(deep)

    # Deduplicate while preserving order
    seen = set()
    unique_patterns = []
    for pattern in patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)

    return unique_patterns


def merge_patterns(
    doc_patterns: list[str] | set[str],
    scope_patterns: list[str] | set[str],
    prioritize_doc: bool = True,
) -> list[str]:
    """Merge and deduplicate patterns from docs and scope.

    Args:
        doc_patterns: Patterns extracted from documentation
        scope_patterns: Patterns from scope template
        prioritize_doc: If True, list doc patterns first (higher priority matching)

    Returns:
        Deduplicated list of patterns, ordered by priority

    Example:
        >>> merge_patterns(['*/cli/*', 'dope/cli/*'], ['*/api/*', '*/cli/*'])
        ['*/cli/*', 'dope/cli/*', '*/api/*']
    """
    # Convert to lists for ordering
    doc_list = list(doc_patterns) if doc_patterns else []
    scope_list = list(scope_patterns) if scope_patterns else []

    # Deduplicate
    seen = set()
    merged = []

    # Add patterns in priority order
    sources = [doc_list, scope_list] if prioritize_doc else [scope_list, doc_list]

    for pattern_list in sources:
        for pattern in pattern_list:
            if pattern not in seen:
                seen.add(pattern)
                merged.append(pattern)

    return merged


def extract_file_paths_from_text(text: str) -> list[str]:
    """Extract file path references from documentation text.

    Identifies paths by looking for common patterns:
    - Unix paths: word/word/file.ext
    - Inline code: `path/to/file`
    - Common extensions: .py, .js, .go, .rs, .java, etc.

    Args:
        text: Documentation text or reference string

    Returns:
        List of normalized file paths (relative, no leading ./)

    Example:
        >>> extract_file_paths_from_text("See dope/cli/main.py for details")
        ['dope/cli/main.py']
        >>> extract_file_paths_from_text("Run `./src/server.js` to start")
        ['src/server.js']
    """
    if not text:
        return []

    paths = []

    # Pattern: path-like strings with at least one slash and optional extension
    # Matches: dope/cli/main.py, src/api/routes, ./scripts/build.sh
    path_pattern = r"\.?/?(?:[a-zA-Z0-9_\-]+/)+[a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9]+)?"

    matches = re.findall(path_pattern, text)

    for match in matches:
        # Clean up match
        cleaned = match.strip("./")

        # Skip if looks like a URL or too short
        if "://" in cleaned or len(cleaned) < 3:
            continue

        # Skip single character directory names (likely false positive)
        parts = cleaned.split("/")
        if any(len(p) <= 1 for p in parts[:-1]):  # Allow short filenames
            continue

        paths.append(cleaned)

    return paths
