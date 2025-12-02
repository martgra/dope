"""Scope-based filtering of code changes for documentation suggestions.

This module provides intelligent filtering of code changes based on their
alignment with the project's documentation scope. It reduces LLM costs by
excluding low-relevance changes and improves suggestion quality by providing
focused, scope-aware context.
"""

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

from dope.core.classification import ChangeCategory, infer_change_category
from dope.models.domain.scope import ScopeTemplate
from dope.models.enums import DocTemplateKey
from dope.models.settings import ScopeFilterSettings


@dataclass
class SectionRelevance:
    """Relevance of a code change to a documentation section.

    Attributes:
        doc_key: Documentation template key
        section_name: Section within the document
        relevance_score: Score from 0-1 indicating alignment strength
        matched_patterns: Code patterns that matched
        matched_categories: Change categories that matched
    """

    doc_key: DocTemplateKey
    section_name: str
    relevance_score: float
    matched_patterns: list[str] = field(default_factory=list)
    matched_categories: set[str] = field(default_factory=set)


class ScopeAlignmentFilter:
    """Filter and score code changes based on scope alignment.

    Uses documentation scope templates to determine which code changes
    are relevant to which documentation sections. Calculates relevance
    scores based on pattern matching, change categories, and magnitude.

    Args:
        scope: Project scope template defining doc structure and triggers
        settings: Filter settings with scoring weights and thresholds

    Example:
        >>> scope = load_scope()
        >>> settings = ScopeFilterSettings()
        >>> filter = ScopeAlignmentFilter(scope, settings)
        >>>
        >>> relevance = filter.get_relevant_sections(
        ...     Path("dope/cli/main.py"),
        ...     magnitude=0.7,
        ...     category=ChangeCategory.CLI
        ... )
        >>> for section in relevance:
        ...     print(f"{section.doc_key}.{section.section_name}: {section.relevance_score}")
    """

    def __init__(self, scope: ScopeTemplate, settings: ScopeFilterSettings | None = None):
        """Initialize filter with scope and settings.

        Args:
            scope: Documentation scope template
            settings: Filter settings (uses defaults if None)
        """
        self._scope = scope
        self._settings = settings or ScopeFilterSettings()
        self._pattern_index: dict[str, list[tuple[DocTemplateKey, str]]] = {}
        self._build_pattern_index()

    def _build_pattern_index(self) -> None:
        """Build inverted index: code_pattern -> [(doc_key, section_name), ...].

        Enables fast lookup of which sections care about a given file pattern.
        """
        for doc_key, doc_template in self._scope.documentation_structure.items():
            for section_name, section in doc_template.sections.items():
                for pattern in section.update_triggers.code_patterns:
                    if pattern not in self._pattern_index:
                        self._pattern_index[pattern] = []
                    self._pattern_index[pattern].append((doc_key, section_name))

    def get_relevant_sections(
        self,
        file_path: Path,
        magnitude: float,
        category: ChangeCategory | None = None,
    ) -> list[SectionRelevance]:
        """Get documentation sections relevant to a code change.

        Returns sections sorted by relevance score (highest first).
        Only includes sections meeting the minimum relevance threshold.

        Args:
            file_path: Path to changed file
            magnitude: Change magnitude score (0-1)
            category: Optional change category (inferred if None)

        Returns:
            List of SectionRelevance objects sorted by score descending

        Example:
            >>> relevance = filter.get_relevant_sections(
            ...     Path("dope/api/routes.py"),
            ...     magnitude=0.8,
            ...     category=ChangeCategory.API
            ... )
            >>> if relevance:
            ...     top = relevance[0]
            ...     print(
            ...         f"Top: {top.doc_key}.{top.section_name} "
            ...         f"({top.relevance_score:.2f})"
            ...     )
        """
        # Infer category if not provided
        if category is None:
            category = infer_change_category(file_path)

        relevant: list[SectionRelevance] = []

        for doc_key, doc_template in self._scope.documentation_structure.items():
            for section_name, section in doc_template.sections.items():
                score, matched_patterns, matched_categories = self._calculate_relevance(
                    file_path=file_path,
                    magnitude=magnitude,
                    category=category,
                    triggers=section.update_triggers,
                )

                # Only include if meets minimum threshold
                if score >= self._settings.min_relevance_score:
                    relevant.append(
                        SectionRelevance(
                            doc_key=doc_key,
                            section_name=section_name,
                            relevance_score=score,
                            matched_patterns=matched_patterns,
                            matched_categories=matched_categories,
                        )
                    )

        # Sort by relevance descending
        return sorted(relevant, key=lambda x: x.relevance_score, reverse=True)

    def _calculate_relevance(
        self,
        file_path: Path,
        magnitude: float,
        category: ChangeCategory | None,
        triggers,
    ) -> tuple[float, list[str], set[str]]:
        """Calculate relevance score for a file against section triggers.

        Score is weighted sum of:
        - Pattern matching (file path matches trigger patterns)
        - Category matching (change category in trigger types)
        - Magnitude matching (change magnitude >= trigger threshold)

        Args:
            file_path: Path to changed file
            magnitude: Change magnitude (0-1)
            category: Change category or None
            triggers: UpdateTriggers from section template

        Returns:
            Tuple of (score, matched_patterns, matched_categories)
        """
        score = 0.0
        matched_patterns: list[str] = []
        matched_categories: set[str] = set()

        path_str = str(file_path)

        # Check pattern matching
        for pattern in triggers.code_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                score += self._settings.pattern_match_weight
                matched_patterns.append(pattern)
                break  # Only count first match

        # Check category matching
        if category and category.value in triggers.change_types:
            score += self._settings.category_match_weight
            matched_categories.add(category.value)

        # Check magnitude threshold
        if magnitude >= triggers.min_magnitude:
            # Scale magnitude contribution by how much it exceeds threshold
            magnitude_factor = min(magnitude / 1.0, 1.0)
            score += self._settings.magnitude_weight * magnitude_factor

        return (min(score, 1.0), matched_patterns, matched_categories)

    def filter_changes(
        self, changes: dict[str, dict]
    ) -> tuple[dict[str, dict], dict[str, list[SectionRelevance]]]:
        """Filter code changes based on scope alignment.

        Calculates relevance for each change and filters out those below
        the minimum threshold. Attaches scope alignment metadata to remaining changes.

        Args:
            changes: Dict of filepath -> change data (must include metadata.magnitude)

        Returns:
            Tuple of (filtered_changes, relevance_map)
            - filtered_changes: Changes meeting relevance threshold with scope metadata
            - relevance_map: filepath -> list of relevant sections

        Example:
            >>> changes = {
            ...     "dope/cli/main.py": {
            ...         "metadata": {"magnitude": 0.7, "classification": "HIGH"}
            ...     }
            ... }
            >>> filtered, relevance = filter.filter_changes(changes)
            >>> print(f"Kept {len(filtered)} of {len(changes)} changes")
        """
        filtered_changes = {}
        relevance_map: dict[str, list[SectionRelevance]] = {}

        for filepath, change_data in changes.items():
            # Skip already-skipped files
            if change_data.get("skipped"):
                continue

            # Extract metadata
            metadata = change_data.get("metadata", {})
            magnitude = metadata.get("magnitude", 0.0)

            # Infer category from path
            category = infer_change_category(Path(filepath))

            # Calculate relevance
            relevant_sections = self.get_relevant_sections(
                file_path=Path(filepath),
                magnitude=magnitude,
                category=category,
            )

            # Only keep changes with relevant sections
            if relevant_sections:
                # Attach scope alignment metadata
                change_data["scope_alignment"] = {
                    "relevant_sections": [
                        {
                            "doc": section.doc_key.value,
                            "section": section.section_name,
                            "relevance": round(section.relevance_score, 3),
                            "matched_patterns": section.matched_patterns,
                            "matched_categories": list(section.matched_categories),
                        }
                        for section in relevant_sections[:5]  # Top 5 most relevant
                    ],
                    "max_relevance": round(relevant_sections[0].relevance_score, 3),
                    "category": category.value if category else None,
                }

                filtered_changes[filepath] = change_data
                relevance_map[filepath] = relevant_sections

        return filtered_changes, relevance_map
