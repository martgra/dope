"""Unit tests for json_state repository - JSON persistence operations."""

import json
from pathlib import Path

import pytest

from dope.repositories.json_state import JsonStateRepository


class TestJsonStateRepository:
    """Tests for JsonStateRepository class."""

    def test_init_with_path(self, temp_dir):
        """Test repository initialization with a path."""
        state_path = temp_dir / "state.json"
        repo = JsonStateRepository(state_path)

        assert repo.path == state_path

    def test_exists_returns_false_when_not_exists(self, temp_dir):
        """Test exists() returns False when file doesn't exist."""
        state_path = temp_dir / "state.json"
        repo = JsonStateRepository(state_path)

        assert not repo.exists()

    def test_exists_returns_true_when_file_exists(self, temp_dir):
        """Test exists() returns True when file exists."""
        state_path = temp_dir / "state.json"
        state_path.write_text("{}")
        repo = JsonStateRepository(state_path)

        assert repo.exists()

    def test_load_returns_empty_dict_when_no_file(self, temp_dir):
        """Test load() returns empty dict when file doesn't exist."""
        state_path = temp_dir / "state.json"
        repo = JsonStateRepository(state_path)

        result = repo.load()

        assert result == {}

    def test_load_returns_stored_state(self, temp_dir):
        """Test load() returns stored state."""
        state_path = temp_dir / "state.json"
        expected = {"key": "value", "nested": {"inner": 42}}
        state_path.write_text(json.dumps(expected))

        repo = JsonStateRepository(state_path)
        result = repo.load()

        assert result == expected

    def test_load_returns_empty_dict_on_invalid_json(self, temp_dir):
        """Test load() returns empty dict when JSON is invalid."""
        state_path = temp_dir / "state.json"
        state_path.write_text("not valid json {")

        repo = JsonStateRepository(state_path)
        result = repo.load()

        assert result == {}

    def test_save_creates_file(self, temp_dir):
        """Test save() creates the state file."""
        state_path = temp_dir / "state.json"
        repo = JsonStateRepository(state_path)

        repo.save({"key": "value"})

        assert state_path.exists()

    def test_save_creates_parent_directories(self, temp_dir):
        """Test save() creates parent directories if needed."""
        state_path = temp_dir / "nested" / "deep" / "state.json"
        repo = JsonStateRepository(state_path)

        repo.save({"key": "value"})

        assert state_path.exists()

    def test_save_writes_valid_json(self, temp_dir):
        """Test save() writes valid JSON that can be loaded."""
        state_path = temp_dir / "state.json"
        repo = JsonStateRepository(state_path)
        data = {"string": "value", "number": 42, "list": [1, 2, 3]}

        repo.save(data)
        loaded = json.loads(state_path.read_text())

        assert loaded == data

    def test_save_uses_utf8_encoding(self, temp_dir):
        """Test save() properly handles unicode characters."""
        state_path = temp_dir / "state.json"
        repo = JsonStateRepository(state_path)
        data = {"unicode": "Hello 世界 🎉"}

        repo.save(data)
        loaded = repo.load()

        assert loaded["unicode"] == "Hello 世界 🎉"


class TestHashComputation:
    """Tests for hash computation methods."""

    def test_compute_hash_consistent(self, temp_dir):
        """Test compute_hash returns same hash for same data."""
        repo = JsonStateRepository(temp_dir / "state.json")

        hash1 = repo.compute_hash({"key": "value"})
        hash2 = repo.compute_hash({"key": "value"})

        assert hash1 == hash2

    def test_compute_hash_different_for_different_data(self, temp_dir):
        """Test compute_hash returns different hashes for different data."""
        repo = JsonStateRepository(temp_dir / "state.json")

        hash1 = repo.compute_hash({"key": "value1"})
        hash2 = repo.compute_hash({"key": "value2"})

        assert hash1 != hash2

    def test_compute_hash_handles_multiple_args(self, temp_dir):
        """Test compute_hash combines multiple arguments."""
        repo = JsonStateRepository(temp_dir / "state.json")

        hash_single = repo.compute_hash({"key": "value"})
        hash_multi = repo.compute_hash({"key": "value"}, [1, 2, 3])

        assert hash_single != hash_multi

    def test_compute_hash_order_independent_for_dicts(self, temp_dir):
        """Test compute_hash is consistent regardless of dict key order."""
        repo = JsonStateRepository(temp_dir / "state.json")

        hash1 = repo.compute_hash({"a": 1, "b": 2})
        hash2 = repo.compute_hash({"b": 2, "a": 1})

        assert hash1 == hash2

    def test_get_stored_hash_when_present(self, temp_dir):
        """Test get_stored_hash returns hash from state."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({"hash": "abc123"}))

        repo = JsonStateRepository(state_path)
        result = repo.get_stored_hash()

        assert result == "abc123"

    def test_get_stored_hash_returns_none_when_missing(self, temp_dir):
        """Test get_stored_hash returns None when hash not in state."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({"other": "data"}))

        repo = JsonStateRepository(state_path)
        result = repo.get_stored_hash()

        assert result is None

    def test_is_hash_valid_returns_true_when_match(self, temp_dir):
        """Test is_hash_valid returns True when hashes match."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({"hash": "abc123"}))

        repo = JsonStateRepository(state_path)
        result = repo.is_hash_valid("abc123")

        assert result is True

    def test_is_hash_valid_returns_false_when_mismatch(self, temp_dir):
        """Test is_hash_valid returns False when hashes don't match."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({"hash": "abc123"}))

        repo = JsonStateRepository(state_path)
        result = repo.is_hash_valid("different_hash")

        assert result is False


class TestDelete:
    """Tests for delete operation."""

    def test_delete_removes_file(self, temp_dir):
        """Test delete() removes the state file."""
        state_path = temp_dir / "state.json"
        state_path.write_text("{}")

        repo = JsonStateRepository(state_path)
        result = repo.delete()

        assert result is True
        assert not state_path.exists()

    def test_delete_returns_false_when_not_exists(self, temp_dir):
        """Test delete() returns False when file doesn't exist."""
        state_path = temp_dir / "state.json"
        repo = JsonStateRepository(state_path)

        result = repo.delete()

        assert result is False
