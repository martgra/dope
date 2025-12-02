"""File classification utilities for intelligent filtering.

This module provides path-based classification of files to determine
processing priority and skip trivial files before expensive LLM operations.
"""

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal


class ChangeCategory(str, Enum):
    """Semantic categorization of code changes.

    Used to match changes against scope section update triggers.
    """

    API = "api"
    CLI = "cli"
    CONFIG = "configuration"
    ARCHITECTURE = "architecture"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    SECURITY = "security"
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"


# File patterns for automatic classification
TRIVIAL_FILE_PATTERNS: dict[str, list[str]] = {
    "test": ["*_test.py", "*.spec.ts", "*.spec.js", "tests/*", "test_*.py", "**/test/**"],
    "lock": ["*.lock", "*.sum", "package-lock.json", "poetry.lock", "Cargo.lock", "yarn.lock"],
    "vendor": ["vendor/*", "node_modules/*", "dist/*", "build/*", ".venv/*", "venv/*"],
    "generated": ["*_pb2.py", "*.pb.go", "*_generated.py", "*.generated.ts"],
    "minified": ["*.min.js", "*.min.css", "*.bundle.js"],
}

DOC_CRITICAL_PATTERNS: dict[str, list[str]] = {
    "readme": ["README.md", "readme.md", "README.rst"],
    "api_docs": ["docs/api/*", "api/*"],
    "entry_points": ["__init__.py", "index.ts", "index.js", "lib.rs", "main.py", "main.go"],
    "config": ["*.config.js", "*.config.ts", "pyproject.toml", "setup.py", "Cargo.toml"],
}


@dataclass
class FileClassification:
    """Classification of a file based on path analysis.

    Attributes:
        classification: Priority level - "SKIP", "HIGH", or "NORMAL"
        reason: Human-readable explanation for the classification
        matched_pattern: The glob pattern that triggered this classification
    """

    classification: Literal["SKIP", "HIGH", "NORMAL"]
    reason: str
    matched_pattern: str | None = None


@dataclass
class ChangeMagnitude:
    """Magnitude of changes in a file.

    Attributes:
        lines_added: Number of lines added
        lines_deleted: Number of lines deleted
        total_lines: Total lines changed (added + deleted)
        is_rename: Whether this change includes a file rename
        score: Significance score from 0.0 to 1.0 (higher = more significant)
        rename_similarity: Similarity percentage for renamed files
        related_docs: Documentation files that may be related to this change
    """

    lines_added: int
    lines_deleted: int
    total_lines: int
    is_rename: bool
    score: float
    rename_similarity: int | None = None
    related_docs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.related_docs is None:
            self.related_docs = []


class FileClassifier:
    """Classifies files based on path patterns for filtering.

    Uses configurable patterns to classify files into categories:
    - SKIP: Trivial files that don't need documentation (tests, locks, vendor)
    - HIGH: Critical files that likely need documentation (README, entry points)
    - NORMAL: Regular files that may need documentation

    Args:
        trivial_patterns: Patterns for files to skip
        critical_patterns: Patterns for high-priority files

    Example:
        >>> classifier = FileClassifier()
        >>> result = classifier.classify(Path("test_utils.py"))
        >>> result.classification
        'SKIP'
        >>> result.reason
        'Trivial file type: test'
    """

    def __init__(
        self,
        trivial_patterns: dict[str, list[str]] | None = None,
        critical_patterns: dict[str, list[str]] | None = None,
    ):
        """Initialize classifier with patterns.

        Args:
            trivial_patterns: Patterns for files to skip (defaults to TRIVIAL_FILE_PATTERNS)
            critical_patterns: Patterns for high-priority files (defaults to DOC_CRITICAL_PATTERNS)
        """
        self._trivial_patterns = trivial_patterns or TRIVIAL_FILE_PATTERNS
        self._critical_patterns = critical_patterns or DOC_CRITICAL_PATTERNS

    def classify(self, file_path: Path) -> FileClassification:
        """Classify a file based on its path.

        Fast path-based classification before any expensive operations.

        Args:
            file_path: Path to classify.

        Returns:
            FileClassification with classification, reason, and matched pattern.
        """
        path_str = str(file_path).lower()

        # Check for trivial files to skip
        for category, patterns in self._trivial_patterns.items():
            for pattern in patterns:
                if fnmatch.fnmatch(path_str, pattern.lower()):
                    return FileClassification(
                        classification="SKIP",
                        reason=f"Trivial file type: {category}",
                        matched_pattern=pattern,
                    )

        # Check for critical files to prioritize
        for category, patterns in self._critical_patterns.items():
            for pattern in patterns:
                if fnmatch.fnmatch(path_str, pattern.lower()):
                    return FileClassification(
                        classification="HIGH",
                        reason=f"Critical file type: {category}",
                        matched_pattern=pattern,
                    )

        # Default to normal priority
        return FileClassification(
            classification="NORMAL",
            reason="Regular file requiring standard analysis",
        )


def calculate_magnitude_score(
    lines_added: int,
    lines_deleted: int,
    is_rename: bool = False,
    rename_similarity: int | None = None,
) -> float:
    """Calculate a significance score for file changes.

    Args:
        lines_added: Number of lines added
        lines_deleted: Number of lines deleted
        is_rename: Whether the file was renamed
        rename_similarity: Similarity percentage for renames

    Returns:
        Score from 0.0 to 1.0, higher means more significant
    """
    total_lines = lines_added + lines_deleted

    # Base score on change volume
    if total_lines == 0:
        score = 0.0
    elif total_lines < 5:
        score = 0.2
    elif total_lines < 20:
        score = 0.4
    elif total_lines < 50:
        score = 0.6
    elif total_lines < 100:
        score = 0.8
    else:
        score = 1.0

    # Reduce score for renames (mostly trivial)
    if is_rename and rename_similarity and rename_similarity > 95:
        score *= 0.3  # Pure rename with minimal changes
    elif is_rename:
        score *= 0.6  # Rename with some changes

    return score


def infer_change_category(file_path: Path) -> ChangeCategory | None:
    """Infer change category from file path patterns.

    Args:
        file_path: Path to analyze

    Returns:
        Inferred ChangeCategory or None if no clear match

    Example:
        >>> infer_change_category(Path("dope/cli/main.py"))
        ChangeCategory.CLI
        >>> infer_change_category(Path("pyproject.toml"))
        ChangeCategory.CONFIG
    """
    path_str = str(file_path).lower()

    # CLI patterns
    if any(pattern in path_str for pattern in ["cli/", "commands/", "_cli.py"]):
        return ChangeCategory.CLI

    # API patterns
    if any(pattern in path_str for pattern in ["api/", "endpoints/", "routes/", "views/"]):
        return ChangeCategory.API

    # Configuration patterns
    if any(
        pattern in path_str
        for pattern in [
            "config",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            ".env",
            "settings",
        ]
    ):
        return ChangeCategory.CONFIG

    # Architecture patterns
    if any(
        pattern in path_str
        for pattern in ["__init__.py", "architecture/", "core/", "models/domain/"]
    ):
        return ChangeCategory.ARCHITECTURE

    # Testing patterns
    if any(
        pattern in path_str
        for pattern in ["test_", "_test.py", "tests/", "test/", ".spec.", "conftest.py"]
    ):
        return ChangeCategory.TESTING

    # Security patterns
    if any(pattern in path_str for pattern in ["security/", "auth", "crypto", "secrets"]):
        return ChangeCategory.SECURITY

    # Deployment patterns
    if any(
        pattern in path_str
        for pattern in ["deploy", "docker", "kubernetes", "k8s", ".yml", ".yaml", "ci/"]
    ):
        return ChangeCategory.DEPLOYMENT

    # Documentation patterns
    if any(pattern in path_str for pattern in ["docs/", "readme", ".md", ".rst"]):
        return ChangeCategory.DOCUMENTATION

    return None
