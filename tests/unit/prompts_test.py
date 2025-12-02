"""Tests for core/prompts.py prompt building utilities."""

from pathlib import Path

from dope.core.prompts import (
    format_file_content,
    format_section,
)


class TestFormatFileContent:
    """Tests for format_file_content function."""

    def test_basic_formatting(self):
        """Test basic file content formatting."""
        result = format_file_content("test.py", "code here")

        expected = "file_path: test.py\n\n<Content>\ncode here\n</Content>"
        assert result == expected

    def test_with_path_object(self):
        """Test formatting works with Path objects."""
        result = format_file_content(Path("src/main.py"), "content")

        assert "file_path: src/main.py" in result

    def test_custom_tag_name(self):
        """Test formatting with custom tag name."""
        result = format_file_content("test.py", "diff", tag_name="Diff")

        assert "file_path: test.py" in result
        assert "<Diff>" in result
        assert "</Diff>" in result

    def test_with_metadata(self):
        """Test formatting with metadata kwargs."""
        result = format_file_content(
            "file.py", "content", tag_name="Content", priority="HIGH", magnitude="0.8"
        )

        assert "file_path: file.py" in result
        assert "priority: HIGH" in result
        assert "magnitude: 0.8" in result
        assert "<Content>" in result

    def test_metadata_order(self):
        """Test that file_path comes before metadata."""
        result = format_file_content("test.py", "x", priority="HIGH")

        lines = result.split("\n")
        assert lines[0] == "file_path: test.py"
        assert lines[1] == "priority: HIGH"


class TestFormatSection:
    """Tests for format_section function."""

    def test_creates_xml_tags(self):
        """Test that format_section creates XML-style tags."""
        result = format_section("instructions", "do the thing")

        assert result == "<instructions>\ndo the thing\n</instructions>"

    def test_with_complex_content(self):
        """Test formatting with multiline content."""
        content = "line 1\nline 2\nline 3"
        result = format_section("scope", content)

        assert result == f"<scope>\n{content}\n</scope>"
