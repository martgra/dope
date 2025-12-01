"""Tests for core/prompts.py prompt building utilities."""

from pathlib import Path

from dope.core.prompts import (
    FileContent,
    PromptBuilder,
    format_file_content,
    format_section,
)


class TestPromptBuilder:
    """Tests for PromptBuilder class."""

    def test_add_section_creates_xml_tags(self):
        """Test that add_section wraps content in XML-style tags."""
        builder = PromptBuilder()
        builder.add_section("scope", "some scope content")

        result = builder.build()

        assert result == "<scope>\nsome scope content\n</scope>"

    def test_add_text_adds_plain_text(self):
        """Test that add_text adds text without wrapping."""
        builder = PromptBuilder()
        builder.add_text("plain text here")

        result = builder.build()

        assert result == "plain text here"

    def test_add_file_formats_with_path_and_content(self):
        """Test that add_file creates standard file format."""
        builder = PromptBuilder()
        builder.add_file("src/main.py", "print('hello')")

        result = builder.build()

        expected = "file_path: src/main.py\n\n<Content>\nprint('hello')\n</Content>"
        assert result == expected

    def test_add_file_with_path_object(self):
        """Test that add_file works with Path objects."""
        builder = PromptBuilder()
        builder.add_file(Path("src/main.py"), "content")

        result = builder.build()

        assert "file_path: src/main.py" in result

    def test_add_file_with_custom_tag_name(self):
        """Test that add_file uses custom tag name."""
        builder = PromptBuilder()
        builder.add_file("file.py", "content", tag_name="Diff")

        result = builder.build()

        assert "<Diff>" in result
        assert "</Diff>" in result

    def test_add_file_with_metadata(self):
        """Test that add_file includes metadata."""
        builder = PromptBuilder()
        builder.add_file("file.py", "content", priority="HIGH", magnitude="0.8")

        result = builder.build()

        assert "priority: HIGH" in result
        assert "magnitude: 0.8" in result

    def test_add_files_adds_multiple(self):
        """Test that add_files handles multiple FileContent objects."""
        files = [
            FileContent("file1.py", "content1"),
            FileContent("file2.py", "content2"),
        ]
        builder = PromptBuilder()
        builder.add_files(files)

        result = builder.build()

        assert "file_path: file1.py" in result
        assert "file_path: file2.py" in result

    def test_add_files_with_metadata(self):
        """Test that add_files includes metadata from FileContent."""
        files = [FileContent("file.py", "content", metadata={"priority": "HIGH"})]
        builder = PromptBuilder()
        builder.add_files(files)

        result = builder.build()

        assert "priority: HIGH" in result

    def test_method_chaining(self):
        """Test that methods return self for chaining."""
        builder = PromptBuilder()
        result = (
            builder.add_section("scope", "scope content")
            .add_text("some text")
            .add_file("file.py", "content")
            .build()
        )

        assert "<scope>" in result
        assert "some text" in result
        assert "file_path: file.py" in result

    def test_build_with_custom_separator(self):
        """Test that build uses custom separator."""
        builder = PromptBuilder()
        builder.add_text("a").add_text("b")

        result = builder.build(separator="\n---\n")

        assert result == "a\n---\nb"

    def test_clear_removes_all_sections(self):
        """Test that clear empties the builder."""
        builder = PromptBuilder()
        builder.add_text("content")
        builder.clear()

        result = builder.build()

        assert result == ""


class TestFormatFileContent:
    """Tests for format_file_content function."""

    def test_basic_formatting(self):
        """Test basic file content formatting."""
        result = format_file_content("test.py", "code here")

        expected = "file_path: test.py\n\n<Content>\ncode here\n</Content>"
        assert result == expected

    def test_custom_tag_name(self):
        """Test formatting with custom tag name."""
        result = format_file_content("test.py", "diff", tag_name="Diff")

        assert "<Diff>" in result
        assert "</Diff>" in result


class TestFormatSection:
    """Tests for format_section function."""

    def test_creates_xml_tags(self):
        """Test that format_section creates XML-style tags."""
        result = format_section("instructions", "do the thing")

        assert result == "<instructions>\ndo the thing\n</instructions>"
