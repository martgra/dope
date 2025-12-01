"""Unit tests for doc_consumer module - documentation file discovery."""

from pathlib import Path

import pytest

from dope.consumers.doc_consumer import DocConsumer
from dope.exceptions import InvalidDirectoryError


class TestDocConsumerInit:
    """Tests for DocConsumer initialization."""

    def test_init_with_valid_directory(self, temp_dir):
        """Test initialization with a valid directory."""
        consumer = DocConsumer(
            temp_dir,
            file_type_filter={".md", ".mdx"},
            exclude_dirs={"node_modules"},
        )

        assert consumer.root_path == temp_dir

    def test_init_raises_for_invalid_directory(self, temp_dir):
        """Test that initialization raises for non-existent directory."""
        with pytest.raises(InvalidDirectoryError):
            DocConsumer(
                temp_dir / "nonexistent",
                file_type_filter={".md"},
                exclude_dirs=set(),
            )

    def test_init_raises_for_file_path(self, temp_file):
        """Test that initialization raises when given a file instead of directory."""
        file_path = temp_file("test.md", "content")

        with pytest.raises(InvalidDirectoryError):
            DocConsumer(
                file_path,
                file_type_filter={".md"},
                exclude_dirs=set(),
            )


class TestDiscoverFiles:
    """Tests for file discovery."""

    def test_discovers_markdown_files(self, temp_dir, temp_file):
        """Test that markdown files are discovered."""
        temp_file("readme.md", "# README")
        temp_file("guide.md", "# Guide")

        consumer = DocConsumer(temp_dir, file_type_filter={".md"}, exclude_dirs=set())
        files = consumer.discover_files()

        file_names = {f.name for f in files}
        assert "readme.md" in file_names
        assert "guide.md" in file_names

    def test_discovers_files_in_subdirectories(self, temp_dir, temp_file):
        """Test that files in subdirectories are discovered."""
        temp_file("docs/api/endpoints.md", "# API")
        temp_file("docs/guide/intro.md", "# Intro")

        consumer = DocConsumer(temp_dir, file_type_filter={".md"}, exclude_dirs=set())
        files = consumer.discover_files()

        file_names = {f.name for f in files}
        assert "endpoints.md" in file_names
        assert "intro.md" in file_names

    def test_filters_by_extension(self, temp_dir, temp_file):
        """Test that only files with matching extensions are discovered."""
        temp_file("readme.md", "# README")
        temp_file("data.json", "{}")
        temp_file("script.py", "print('hello')")

        consumer = DocConsumer(temp_dir, file_type_filter={".md"}, exclude_dirs=set())
        files = consumer.discover_files()

        file_names = {f.name for f in files}
        assert "readme.md" in file_names
        assert "data.json" not in file_names
        assert "script.py" not in file_names

    def test_supports_multiple_extensions(self, temp_dir, temp_file):
        """Test filtering with multiple file extensions."""
        temp_file("readme.md", "# README")
        temp_file("guide.mdx", "# Guide")
        temp_file("data.txt", "data")

        consumer = DocConsumer(temp_dir, file_type_filter={".md", ".mdx"}, exclude_dirs=set())
        files = consumer.discover_files()

        file_names = {f.name for f in files}
        assert "readme.md" in file_names
        assert "guide.mdx" in file_names
        assert "data.txt" not in file_names

    def test_excludes_directories(self, temp_dir, temp_file):
        """Test that specified directories are excluded."""
        temp_file("readme.md", "# README")
        temp_file("node_modules/pkg/readme.md", "# Package")
        temp_file(".venv/docs/api.md", "# API")

        consumer = DocConsumer(
            temp_dir, file_type_filter={".md"}, exclude_dirs={"node_modules", ".venv"}
        )
        files = consumer.discover_files()

        file_paths = [str(f) for f in files]
        assert any("readme.md" in p and "node_modules" not in p for p in file_paths)
        assert not any("node_modules" in p for p in file_paths)
        assert not any(".venv" in p for p in file_paths)

    def test_exclude_dirs_case_insensitive(self, temp_dir, temp_file):
        """Test that directory exclusion is case-insensitive."""
        temp_file("Node_Modules/pkg/readme.md", "# Package")

        consumer = DocConsumer(
            temp_dir, file_type_filter={".md"}, exclude_dirs={"node_modules"}
        )
        files = consumer.discover_files()

        # Should exclude Node_Modules even though pattern is node_modules
        file_paths = [str(f) for f in files]
        assert not any("node_modules" in p.lower() for p in file_paths)

    def test_returns_empty_for_empty_directory(self, temp_dir):
        """Test that empty directory returns empty list."""
        consumer = DocConsumer(temp_dir, file_type_filter={".md"}, exclude_dirs=set())
        files = consumer.discover_files()

        assert files == []

    def test_custom_file_filter_parameter(self, temp_dir, temp_file):
        """Test passing additional file filter at discover time."""
        temp_file("readme.md", "# README")
        temp_file("notes.txt", "notes")

        consumer = DocConsumer(temp_dir, file_type_filter={".md"}, exclude_dirs=set())

        # Add .txt at discover time
        files = consumer.discover_files(file_filter={".txt"})

        file_names = {f.name for f in files}
        assert "readme.md" in file_names
        assert "notes.txt" in file_names

    def test_custom_exclude_dirs_parameter(self, temp_dir, temp_file):
        """Test passing additional exclude dirs at discover time."""
        temp_file("readme.md", "# README")
        temp_file("build/docs.md", "# Build docs")

        consumer = DocConsumer(temp_dir, file_type_filter={".md"}, exclude_dirs=set())

        # Exclude build at discover time
        files = consumer.discover_files(exclude_dirs={"build"})

        file_paths = [str(f) for f in files]
        assert not any("build" in p for p in file_paths)


class TestGetContent:
    """Tests for get_content method."""

    def test_returns_file_content_as_bytes(self, temp_dir, temp_file):
        """Test that get_content returns file content as bytes."""
        content = "# Hello World\n\nSome content."
        file_path = temp_file("readme.md", content)

        consumer = DocConsumer(temp_dir, file_type_filter={".md"}, exclude_dirs=set())
        result = consumer.get_content(file_path)

        assert result == content.encode("utf-8")

    def test_handles_unicode_content(self, temp_dir, temp_file):
        """Test that get_content handles unicode content."""
        content = "# 你好世界\n\n🎉 Emoji content."
        file_path = temp_file("unicode.md", content)

        consumer = DocConsumer(temp_dir, file_type_filter={".md"}, exclude_dirs=set())
        result = consumer.get_content(file_path)

        assert result == content.encode("utf-8")

    def test_handles_binary_content(self, temp_dir):
        """Test that get_content handles binary files."""
        file_path = temp_dir / "binary.bin"
        binary_content = bytes([0x00, 0xFF, 0x42, 0x00])
        file_path.write_bytes(binary_content)

        consumer = DocConsumer(temp_dir, file_type_filter={".bin"}, exclude_dirs=set())
        result = consumer.get_content(file_path)

        assert result == binary_content
