"""Common prompt building utilities.

This module provides reusable patterns for constructing LLM prompts
across different services, ensuring consistency in formatting.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileContent:
    """Represents a file with its content for prompt inclusion."""

    file_path: str | Path
    content: str
    metadata: dict[str, str] | None = None


class PromptBuilder:
    """Builder for constructing prompts with file content sections.

    Provides consistent formatting for including file content, metadata,
    and structured sections in LLM prompts.

    Example:
        >>> builder = PromptBuilder()
        >>> builder.add_section("scope", scope_content)
        >>> builder.add_file("config.py", config_content, priority="HIGH")
        >>> prompt = builder.build()
    """

    def __init__(self) -> None:
        """Initialize an empty prompt builder."""
        self._sections: list[str] = []

    def add_section(self, name: str, content: str) -> "PromptBuilder":
        """Add a named section with XML-style tags.

        Args:
            name: Section name (used as tag name).
            content: Content to include in the section.

        Returns:
            Self for method chaining.
        """
        self._sections.append(f"<{name}>\n{content}\n</{name}>")
        return self

    def add_text(self, text: str) -> "PromptBuilder":
        """Add plain text without wrapping.

        Args:
            text: Text to add to the prompt.

        Returns:
            Self for method chaining.
        """
        self._sections.append(text)
        return self

    def add_file(
        self,
        file_path: str | Path,
        content: str,
        tag_name: str = "Content",
        **metadata: str,
    ) -> "PromptBuilder":
        """Add file content with consistent formatting.

        Args:
            file_path: Path to the file.
            content: File content to include.
            tag_name: Tag name for the content wrapper (default: "Content").
            **metadata: Additional metadata as key=value pairs.

        Returns:
            Self for method chaining.
        """
        parts = [f"file_path: {file_path}"]

        for key, value in metadata.items():
            parts.append(f"{key}: {value}")

        parts.append(f"\n<{tag_name}>\n{content}\n</{tag_name}>")

        self._sections.append("\n".join(parts))
        return self

    def add_files(
        self,
        files: list[FileContent],
        tag_name: str = "Content",
    ) -> "PromptBuilder":
        """Add multiple files with consistent formatting.

        Args:
            files: List of FileContent objects to include.
            tag_name: Tag name for content wrappers (default: "Content").

        Returns:
            Self for method chaining.
        """
        for file in files:
            metadata = file.metadata or {}
            self.add_file(file.file_path, file.content, tag_name, **metadata)
        return self

    def build(self, separator: str = "\n\n") -> str:
        """Build the final prompt string.

        Args:
            separator: String to join sections with (default: double newline).

        Returns:
            Complete prompt string.
        """
        return separator.join(self._sections)

    def clear(self) -> "PromptBuilder":
        """Clear all sections.

        Returns:
            Self for method chaining.
        """
        self._sections = []
        return self


def format_file_content(
    file_path: str | Path,
    content: str,
    tag_name: str = "Content",
) -> str:
    """Format file content for prompt inclusion.

    This is a convenience function for simple single-file formatting.

    Args:
        file_path: Path to the file.
        content: File content to include.
        tag_name: Tag name for the content wrapper.

    Returns:
        Formatted string with file path and content.
    """
    return f"file_path: {file_path}\n\n<{tag_name}>\n{content}\n</{tag_name}>"


def format_section(name: str, content: str) -> str:
    """Format a section with XML-style tags.

    Args:
        name: Section name (used as tag name).
        content: Content to include in the section.

    Returns:
        Formatted section string.
    """
    return f"<{name}>\n{content}\n</{name}>"
