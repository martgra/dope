"""Unit tests for classification module - file classification and magnitude scoring."""

from pathlib import Path

import pytest

from dope.core.classification import (
    ChangeMagnitude,
    FileClassification,
    FileClassifier,
    calculate_magnitude_score,
)


class TestFileClassifier:
    """Tests for FileClassifier class."""

    @pytest.fixture
    def classifier(self):
        """Create a default classifier instance."""
        return FileClassifier()

    def test_classify_test_file_patterns(self, classifier):
        """Test that test files are classified as SKIP."""
        test_paths = [
            Path("test_example.py"),
            Path("example_test.py"),
            Path("tests/unit/test_api.py"),
            Path("spec/feature.spec.ts"),
            Path("component.spec.js"),
        ]

        for path in test_paths:
            result = classifier.classify(path)
            assert result.classification == "SKIP", f"Failed for {path}"
            assert "test" in result.reason.lower()

    def test_classify_lock_files(self, classifier):
        """Test that lock files are classified as SKIP."""
        lock_paths = [
            Path("package-lock.json"),
            Path("poetry.lock"),
            Path("Cargo.lock"),
            Path("go.sum"),
        ]

        for path in lock_paths:
            result = classifier.classify(path)
            assert result.classification == "SKIP", f"Failed for {path}"
            assert "lock" in result.reason.lower()

    def test_classify_vendor_directories(self, classifier):
        """Test that vendor/dependency directories are classified as SKIP."""
        vendor_paths = [
            Path("node_modules/lodash/index.js"),
            Path("vendor/github.com/pkg/errors/errors.go"),
            Path(".venv/lib/site-packages/requests/api.py"),
            Path("dist/bundle.js"),
        ]

        for path in vendor_paths:
            result = classifier.classify(path)
            assert result.classification == "SKIP", f"Failed for {path}"
            assert "vendor" in result.reason.lower()

    def test_classify_critical_files_as_high(self, classifier):
        """Test that critical files are classified as HIGH priority."""
        critical_paths = [
            Path("README.md"),
            Path("__init__.py"),
            Path("index.ts"),
            Path("main.py"),
            Path("pyproject.toml"),
        ]

        for path in critical_paths:
            result = classifier.classify(path)
            assert result.classification == "HIGH", f"Failed for {path}"

    def test_classify_normal_source_files(self, classifier):
        """Test that regular source files are classified as NORMAL."""
        normal_paths = [
            Path("src/api/handlers.py"),
            Path("lib/utils.ts"),
            Path("internal/service.go"),
            Path("models/user.rb"),
        ]

        for path in normal_paths:
            result = classifier.classify(path)
            assert result.classification == "NORMAL", f"Failed for {path}"

    def test_case_insensitive_matching(self, classifier):
        """Test that classification is case-insensitive."""
        assert classifier.classify(Path("README.MD")).classification == "HIGH"
        assert classifier.classify(Path("Test_Example.py")).classification == "SKIP"
        assert classifier.classify(Path("PACKAGE-LOCK.JSON")).classification == "SKIP"

    def test_matched_pattern_recorded(self, classifier):
        """Test that matched pattern is recorded in classification."""
        result = classifier.classify(Path("test_api.py"))

        assert result.matched_pattern is not None
        assert "test" in result.matched_pattern.lower()


class TestCustomPatterns:
    """Tests for FileClassifier with custom patterns."""

    def test_custom_trivial_patterns(self):
        """Test classifier with custom trivial patterns."""
        custom_trivial = {
            "custom_skip": ["*.skip.py", "skip_*.txt"],
        }
        classifier = FileClassifier(trivial_patterns=custom_trivial)

        assert classifier.classify(Path("example.skip.py")).classification == "SKIP"
        assert classifier.classify(Path("skip_this.txt")).classification == "SKIP"
        # Default patterns should not apply
        assert classifier.classify(Path("test_api.py")).classification == "NORMAL"

    def test_custom_critical_patterns(self):
        """Test classifier with custom critical patterns."""
        custom_critical = {
            "important": ["*.important.py", "CRITICAL.md"],
        }
        classifier = FileClassifier(critical_patterns=custom_critical)

        assert classifier.classify(Path("file.important.py")).classification == "HIGH"
        assert classifier.classify(Path("CRITICAL.md")).classification == "HIGH"


class TestCalculateMagnitudeScore:
    """Tests for calculate_magnitude_score function."""

    def test_zero_lines_returns_zero(self):
        """Test that zero lines changed returns zero score."""
        score = calculate_magnitude_score(0, 0)
        assert score == 0.0

    def test_small_change_low_score(self):
        """Test that small changes get low scores."""
        score = calculate_magnitude_score(2, 1)
        assert score == 0.2

    def test_medium_change_medium_score(self):
        """Test that medium changes get medium scores."""
        score = calculate_magnitude_score(10, 5)
        assert 0.3 < score < 0.7

    def test_large_change_high_score(self):
        """Test that large changes get high scores."""
        score = calculate_magnitude_score(80, 40)
        assert score >= 0.8

    def test_very_large_change_max_score(self):
        """Test that very large changes get maximum score."""
        score = calculate_magnitude_score(200, 100)
        assert score == 1.0

    def test_rename_reduces_score(self):
        """Test that renames reduce the significance score."""
        base_score = calculate_magnitude_score(50, 50)
        rename_score = calculate_magnitude_score(50, 50, is_rename=True, rename_similarity=98)

        assert rename_score < base_score

    def test_high_similarity_rename_strongly_reduced(self):
        """Test that high-similarity renames are strongly reduced."""
        # 96% similarity should give 0.3x multiplier
        score = calculate_magnitude_score(100, 0, is_rename=True, rename_similarity=96)
        # Base would be 0.8 for 100 lines, * 0.3 = 0.24
        assert score <= 0.3

    def test_partial_rename_moderately_reduced(self):
        """Test that partial renames (with content changes) are moderately reduced."""
        # 85% similarity (below 95%) should give 0.6x multiplier
        score = calculate_magnitude_score(50, 50, is_rename=True, rename_similarity=85)
        base_score = calculate_magnitude_score(50, 50)

        assert score == base_score * 0.6


class TestChangeMagnitudeDataclass:
    """Tests for ChangeMagnitude dataclass."""

    def test_basic_creation(self):
        """Test creating a ChangeMagnitude instance."""
        magnitude = ChangeMagnitude(
            lines_added=10,
            lines_deleted=5,
            total_lines=15,
            is_rename=False,
            score=0.5,
        )

        assert magnitude.lines_added == 10
        assert magnitude.lines_deleted == 5
        assert magnitude.total_lines == 15
        assert not magnitude.is_rename
        assert magnitude.score == 0.5

    def test_default_related_docs(self):
        """Test that related_docs defaults to empty list."""
        magnitude = ChangeMagnitude(
            lines_added=10,
            lines_deleted=5,
            total_lines=15,
            is_rename=False,
            score=0.5,
        )

        assert magnitude.related_docs == []

    def test_with_rename_info(self):
        """Test ChangeMagnitude with rename information."""
        magnitude = ChangeMagnitude(
            lines_added=0,
            lines_deleted=0,
            total_lines=0,
            is_rename=True,
            score=0.1,
            rename_similarity=95,
        )

        assert magnitude.is_rename
        assert magnitude.rename_similarity == 95


class TestFileClassificationDataclass:
    """Tests for FileClassification dataclass."""

    def test_basic_creation(self):
        """Test creating a FileClassification instance."""
        classification = FileClassification(
            classification="SKIP",
            reason="Test file",
            matched_pattern="test_*.py",
        )

        assert classification.classification == "SKIP"
        assert classification.reason == "Test file"
        assert classification.matched_pattern == "test_*.py"

    def test_optional_matched_pattern(self):
        """Test that matched_pattern is optional."""
        classification = FileClassification(
            classification="NORMAL",
            reason="Regular file",
        )

        assert classification.matched_pattern is None
