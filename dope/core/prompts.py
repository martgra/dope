"""Common prompt building utilities.

This module provides reusable functions for constructing LLM prompts
across different services, ensuring consistency in formatting.
"""

from pathlib import Path


def format_section(name: str, content: str) -> str:
    r"""Format a section with XML-style tags.

    Args:
        name: Section name (used as tag name).
        content: Content to include in the section.

    Returns:
        Formatted section string.

    Example:
        >>> format_section("scope", "Update user auth")
        '<scope>\nUpdate user auth\n</scope>'
    """
    return f"<{name}>\n{content}\n</{name}>"


def format_file_content(
    file_path: str | Path,
    content: str,
    tag_name: str = "Content",
    **metadata: str,
) -> str:
    r"""Format file content with metadata for prompt inclusion.

    Args:
        file_path: Path to the file.
        content: File content to include.
        tag_name: Tag name for the content wrapper (default: "Content").
        **metadata: Additional metadata as key=value pairs.

    Returns:
        Formatted string with file path, metadata, and content.

    Example:
        >>> format_file_content("config.py", "DEBUG=True", priority="HIGH")
        'file_path: config.py\npriority: HIGH\n\n<Content>\nDEBUG=True\n</Content>'
    """
    parts = [f"file_path: {file_path}"]

    for key, value in metadata.items():
        parts.append(f"{key}: {value}")

    parts.append(f"\n<{tag_name}>\n{content}\n</{tag_name}>")

    return "\n".join(parts)
