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
    """

    def __init__(self, index_path: Path | None = None):
        """Initialize term index.

        Args:
            index_path: Optional path to persist index as JSON.
        """
        self.index_path = index_path
        self.term_to_docs: dict[str, set[str]] = defaultdict(set)
        self.doc_hashes: dict[str, str] = {}  # Track doc versions

    def build_from_state(self, doc_state: dict) -> None:
        """Build term index from documentation state.

        Extracts terms from:
        - DocSummary.references (commands, files, functions, config values)
        - Section names (major documentation topics)

        Args:
            doc_state: Documentation state from DescriberService
        """
        self.term_to_docs.clear()
        self.doc_hashes.clear()

        for doc_path, doc_data in doc_state.items():
            # Skip if no summary or if skipped
            if not doc_data.get("summary") or doc_data.get("skipped"):
                continue

            # Track doc version
            self.doc_hashes[doc_path] = doc_data.get("hash", "")

            summary = doc_data["summary"]
            sections = summary.get("sections", [])

            for section in sections:
                # Extract from references
                references = section.get("references", [])
                for ref in references:
                    # Normalize and extract terms
                    terms = self._extract_terms(ref)
                    for term in terms:
                        self.term_to_docs[term].add(doc_path)

                # Extract from section names (major topics)
                section_name = section.get("section_name", "")
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
