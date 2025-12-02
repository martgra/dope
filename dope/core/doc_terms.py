"""Documentation term indexing for context-aware code change scoring.

Extracts significant terms from documentation and uses them to identify
when code changes touch documented concepts, boosting their relevance.
"""

import json
import re
from collections import defaultdict
from pathlib import Path


class DocTermIndex:
    """Index of significant terms extracted from documentation.

    Builds an inverted index: term -> set of doc files mentioning it.
    Used to boost significance of code changes that touch documented concepts.
    Also extracts code path patterns for language-agnostic scope filtering.
    """

    def __init__(self, index_path: Path | None = None):
        """Initialize term index.

        Args:
            index_path: Optional path to persist index as JSON.
        """
        self.index_path = index_path
        self.term_to_docs: dict[str, set[str]] = defaultdict(set)
        self.doc_hashes: dict[str, str] = {}  # Track doc versions
        self.code_patterns: dict[str, set[str]] = defaultdict(set)  # category -> patterns

    def build_from_state(self, doc_state: dict, extract_patterns: bool = True) -> None:  # pylint: disable=too-many-locals
        """Build term index from documentation state.

        Extracts terms from:
        - DocSummary.references (commands, files, functions, config values)
        - Section names (major documentation topics)

        Optionally extracts code patterns from file path references.

        Args:
            doc_state: Documentation state from DescriberService
            extract_patterns: If True, extract code patterns from references
        """
        self.term_to_docs.clear()
        self.doc_hashes.clear()
        self.code_patterns.clear()

        for doc_path, doc_data in doc_state.items():
            # Skip if no summary or if skipped
            if not doc_data.get("summary") or doc_data.get("skipped"):
                continue

            # Track doc version
            self.doc_hashes[doc_path] = doc_data.get("hash", "")

            summary = doc_data["summary"]
            sections = summary.get("sections", [])

            for section in sections:
                section_name = section.get("section_name", "")

                # Extract from references
                references = section.get("references", [])
                for ref in references:
                    # Normalize and extract terms
                    terms = self._extract_terms(ref)
                    for term in terms:
                        self.term_to_docs[term].add(doc_path)

                    # Extract code patterns if enabled
                    if extract_patterns:
                        patterns = self._extract_code_patterns(ref, section_name)
                        for category, pattern_set in patterns.items():
                            self.code_patterns[category].update(pattern_set)

                # Extract from section names (major topics)
                if section_name:
                    terms = self._extract_terms(section_name)
                    for term in terms:
                        self.term_to_docs[term].add(doc_path)

    def _extract_terms(self, text: str) -> set[str]:
        """Extract searchable terms from text.

        Extracts:
        - Words with 3+ characters
        - Preserves case for camelCase/PascalCase
        - Splits snake_case and kebab-case
        - Extracts from file paths

        Args:
            text: Text to extract terms from

        Returns:
            Set of normalized terms
        """
        if not text:
            return set()

        terms = set()

        # Split into tokens first to handle sentences
        tokens = text.split()

        for token in tokens:
            # Extract file paths and split into components
            # Example: "dope/cli/scan.py" -> ["dope", "cli", "scan", "py"]
            if "/" in token or "\\" in token:
                path_parts = re.split(r"[/\\.]", token)
                for part in path_parts:
                    if len(part) >= 3:
                        terms.add(part.lower())

            # Split camelCase and PascalCase but preserve original
            # Example: "DocSummary" -> ["DocSummary", "doc", "summary"]
            camel_words = re.findall(r"[A-Z][a-z]+|[a-z]+", token)
            for word in camel_words:
                if len(word) >= 3:
                    terms.add(word.lower())

            # Split snake_case and kebab-case
            snake_words = re.split(r"[_\-]", token)
            for word in snake_words:
                if len(word) >= 3:
                    terms.add(word.lower())

            # Extract whole words (3+ chars)
            words = re.findall(r"\b[a-zA-Z]{3,}\b", token)
            for word in words:
                terms.add(word.lower())

        return terms

    def _extract_code_patterns(self, text: str, section_name: str) -> dict[str, set[str]]:
        """Extract code patterns from documentation text.

        Identifies file paths in references and generates normalized glob patterns.
        Attempts to infer category from section name context.

        Args:
            text: Reference text that may contain file paths
            section_name: Section name for category inference

        Returns:
            Dictionary mapping categories to sets of glob patterns
        """
        from dope.core.pattern_utils import extract_file_paths_from_text, normalize_code_path

        patterns_by_category: dict[str, set[str]] = defaultdict(set)

        # Extract file paths from text
        file_paths = extract_file_paths_from_text(text)

        if not file_paths:
            return patterns_by_category

        # Infer category from section name
        category = self._infer_category_from_section(section_name)

        # Generate patterns for each file path
        for file_path in file_paths:
            normalized = normalize_code_path(file_path)
            patterns_by_category[category].update(normalized)

        return patterns_by_category

    def _infer_category_from_section(self, section_name: str) -> str:
        """Infer change category from section name.

        Args:
            section_name: Documentation section name

        Returns:
            Category string (api, cli, config, architecture, etc.)
        """
        section_lower = section_name.lower()

        # Category keywords (order matters - check specific before general)
        category_keywords = {
            "cli": ["command", "cli", "arguments", "flags", "option"],
            "api": ["api", "endpoint", "route", "rest", "graphql", "http"],
            "config": ["config", "setting", "environment", "option"],
            "architecture": ["architecture", "design", "structure", "pattern"],
            "testing": ["test", "testing", "pytest", "unittest"],
            "documentation": ["document", "readme", "guide", "tutorial"],
            "dependencies": ["dependency", "package", "requirement", "install"],
            "performance": ["performance", "optimization", "speed", "benchmark"],
            "security": ["security", "auth", "permission", "credential"],
        }

        # Check for keyword matches
        for category, keywords in category_keywords.items():
            if any(keyword in section_lower for keyword in keywords):
                return category

        # Default to general if no match
        return "general"

    def get_relevant_docs(self, code_diff: str) -> list[tuple[str, int]]:
        """Find docs that mention terms appearing in code diff.

        Args:
            code_diff: Git diff output to analyze

        Returns:
            List of (doc_path, match_count) tuples, sorted by relevance
        """
        if not code_diff or not self.term_to_docs:
            return []

        # Extract terms from diff
        diff_terms = self._extract_terms(code_diff)

        # Count matches per doc
        doc_matches: dict[str, int] = defaultdict(int)
        for term in diff_terms:
            if term in self.term_to_docs:
                for doc_path in self.term_to_docs[term]:
                    doc_matches[doc_path] += 1

        # Sort by match count (most relevant first)
        sorted_matches = sorted(doc_matches.items(), key=lambda x: x[1], reverse=True)

        return sorted_matches

    def save(self) -> None:
        """Save term index to JSON file."""
        if not self.index_path:
            return

        # Convert sets to lists for JSON serialization
        serializable_index = {
            "term_to_docs": {term: list(docs) for term, docs in self.term_to_docs.items()},
            "doc_hashes": self.doc_hashes,
            "code_patterns": {
                category: list(patterns) for category, patterns in self.code_patterns.items()
            },
        }

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with self.index_path.open("w") as f:
            json.dump(serializable_index, f, indent=2)

    def load(self) -> bool:
        """Load term index from JSON file.

        Returns:
            True if loaded successfully, False if file doesn't exist
        """
        if not self.index_path or not self.index_path.exists():
            return False

        try:
            with self.index_path.open("r") as f:
                data = json.load(f)

            # Convert lists back to sets
            self.term_to_docs = defaultdict(
                set, {term: set(docs) for term, docs in data.get("term_to_docs", {}).items()}
            )
            self.doc_hashes = data.get("doc_hashes", {})
            self.code_patterns = defaultdict(
                set,
                {
                    category: set(patterns)
                    for category, patterns in data.get("code_patterns", {}).items()
                },
            )
            return True
        except (json.JSONDecodeError, KeyError):
            return False

    def is_stale(self, doc_state: dict) -> bool:
        """Check if index needs rebuilding based on doc changes.

        Args:
            doc_state: Current documentation state

        Returns:
            True if any doc hashes have changed
        """
        if not self.doc_hashes:
            return True

        for doc_path, doc_data in doc_state.items():
            # Skip files without summaries (same as build_from_state)
            if not doc_data.get("summary") or doc_data.get("skipped"):
                continue

            current_hash = doc_data.get("hash", "")
            cached_hash = self.doc_hashes.get(doc_path, "")

            if current_hash != cached_hash:
                return True

        return False

    def filter_relevant_docs(  # pylint: disable=too-many-locals,too-many-branches
        self,
        code_changes: dict[str, dict],
        doc_state: dict[str, dict],
        min_match_threshold: int = 3,
    ) -> dict[str, dict]:
        """Filter documentation files based on relevance to code changes.

        Uses term matching to identify docs that reference concepts touched by code changes.
        Applies conservative filtering using weighted combination: includes docs if they have
        sufficient term matches OR are high priority OR have scope relevance.

        Args:
            code_changes: Dictionary of code file paths to change data with summaries
            doc_state: Dictionary of doc file paths to doc data with summaries
            min_match_threshold: Minimum term matches required to include doc (default: 3)

        Returns:
            Filtered dictionary of relevant doc files with added 'term_relevance' metadata

        Example:
            >>> index = DocTermIndex(Path(".dope/doc-terms.json"))
            >>> index.load()
            >>> relevant_docs = index.filter_relevant_docs(
            ...     code_changes={"dope/cli/main.py": {...}},
            ...     doc_state={"docs/cli.md": {...}, "docs/api.md": {...}},
            ...     min_match_threshold=3
            ... )
            >>> len(relevant_docs)  # Only docs with sufficient matches
            1
        """
        if not self.term_to_docs or not code_changes:
            # No index or no changes - return all docs (safe default)
            return doc_state

        # Extract all terms from code changes
        all_code_terms = set()
        for _file_path, change_data in code_changes.items():
            # Extract terms from summary if available
            summary = change_data.get("summary")
            if summary:
                # Get summary text from various possible structures
                if isinstance(summary, dict):
                    # CodeChanges model structure
                    for change in summary.get("specific_changes", []):
                        if isinstance(change, dict):
                            all_code_terms.update(self._extract_terms(change.get("name", "")))
                            all_code_terms.update(self._extract_terms(change.get("summary", "")))
                    for impact in summary.get("functional_impact", []):
                        all_code_terms.update(self._extract_terms(impact))
                elif isinstance(summary, str):
                    all_code_terms.update(self._extract_terms(summary))

        # Score each doc based on term matches
        doc_scores: dict[str, int] = {}
        for doc_path in doc_state:
            match_count = 0
            for term in all_code_terms:
                if term in self.term_to_docs and doc_path in self.term_to_docs[term]:
                    match_count += 1
            doc_scores[doc_path] = match_count

        # Filter docs using conservative approach
        filtered_docs = {}
        for doc_path, doc_data in doc_state.items():
            match_count = doc_scores.get(doc_path, 0)

            # Conservative filtering: include if ANY condition met
            include = False

            # Condition 1: Sufficient term matches
            if match_count >= min_match_threshold:
                include = True

            # Condition 2: High priority (likely README or critical doc)
            if doc_data.get("priority") == "HIGH":
                include = True

            # Condition 3: Has scope relevance (from previous filtering)
            if doc_data.get("scope_alignment", {}).get("max_relevance", 0) > 0:
                include = True

            if include:
                # Add term relevance metadata
                doc_data_copy = dict(doc_data)
                doc_data_copy["term_relevance"] = {
                    "match_count": match_count,
                    "matched_terms": match_count > 0,
                }
                filtered_docs[doc_path] = doc_data_copy

        return filtered_docs


class DocTermIndexBuilder:
    """Builder for creating and updating DocTermIndex from documentation state.

    Provides a clean interface for building the term index, separate from
    the index itself. Use this when you need explicit control over when
    the index is built.

    Example:
        >>> builder = DocTermIndexBuilder(index_path, extract_patterns=True)
        >>> builder.build_if_needed(doc_state)
    """

    def __init__(self, index_path: Path, extract_patterns: bool = True):
        """Initialize builder with index path.

        Args:
            index_path: Path where index will be persisted.
            extract_patterns: If True, extract code patterns from docs
        """
        self._index_path = index_path
        self._extract_patterns = extract_patterns

    def build_if_needed(self, doc_state: dict) -> bool:
        """Build and save index if it's stale or doesn't exist.

        Args:
            doc_state: Documentation state with summaries.

        Returns:
            True if index was rebuilt, False if cache was valid.
        """
        index = DocTermIndex(self._index_path)

        # Check if we can use cached index
        if index.load() and not index.is_stale(doc_state):
            return False

        # Build and save
        index.build_from_state(doc_state, extract_patterns=self._extract_patterns)
        index.save()
        return True

    def force_build(self, doc_state: dict) -> None:
        """Force rebuild of index regardless of cache state.

        Args:
            doc_state: Documentation state with summaries.
        """
        index = DocTermIndex(self._index_path)
        index.build_from_state(doc_state, extract_patterns=self._extract_patterns)
        index.save()
