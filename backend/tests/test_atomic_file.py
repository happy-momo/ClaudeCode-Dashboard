"""Tests for atomic file utilities."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from utils.atomic_file import (
    atomic_write_json,
    atomic_write_text,
    create_backup,
    patch_json_file,
    read_json_file,
    read_text_file,
    write_markdown,
)


@pytest.fixture
def tmp_path():
    """Provide a temporary directory for each test."""
    d = Path(tempfile.mkdtemp())
    yield d
    # Cleanup
    import shutil
    shutil.rmtree(d, ignore_errors=True)


class TestAtomicWriteText:
    def test_writes_content(self, tmp_path):
        target = tmp_path / "test.txt"
        atomic_write_text(target, "hello world")
        assert target.read_text() == "hello world"

    def test_creates_parent_dirs(self, tmp_path):
        target = tmp_path / "a" / "b" / "c.txt"
        atomic_write_text(target, "nested")
        assert target.read_text() == "nested"

    def test_overwrites_existing(self, tmp_path):
        target = tmp_path / "x.txt"
        target.write_text("old")
        atomic_write_text(target, "new")
        assert target.read_text() == "new"

    def test_file_is_valid_after_write(self, tmp_path):
        """After atomic write, the file content should be complete (not truncated)."""
        target = tmp_path / "large.txt"
        content = "line\n" * 10000
        atomic_write_text(target, content)
        assert target.read_text() == content


class TestAtomicWriteJson:
    def test_writes_valid_json(self, tmp_path):
        target = tmp_path / "data.json"
        data = {"key": "value", "list": [1, 2, 3]}
        atomic_write_json(target, data)
        loaded = json.loads(target.read_text())
        assert loaded == data

    def test_preserves_indent(self, tmp_path):
        target = tmp_path / "indent.json"
        atomic_write_json(target, {"a": 1}, indent=4)
        text = target.read_text()
        assert "    " in text  # 4-space indent present


class TestReadJsonFile:
    def test_reads_existing_file(self, tmp_path):
        target = tmp_path / "data.json"
        target.write_text('{"a": 1}')
        assert read_json_file(target) == {"a": 1}

    def test_returns_default_when_missing(self, tmp_path):
        assert read_json_file(tmp_path / "missing.json") is None
        assert read_json_file(tmp_path / "missing.json", default=42) == 42

    def test_returns_default_when_malformed(self, tmp_path):
        target = tmp_path / "bad.json"
        target.write_text("{bad json}")
        assert read_json_file(target) is None

    def test_returns_default_when_empty(self, tmp_path):
        target = tmp_path / "empty.json"
        target.write_text("")
        assert read_json_file(target) is None


class TestPatchJsonFile:
    def test_adds_key(self, tmp_path):
        target = tmp_path / "patch.json"
        target.write_text('{"a": 1}')

        result = patch_json_file(target, lambda d: {**d, "b": 2})
        assert result == {"a": 1, "b": 2}
        assert json.loads(target.read_text()) == {"a": 1, "b": 2}

    def test_preserves_unknown_fields(self, tmp_path):
        """patch_json_file must not overwrite fields not in the patch."""
        target = tmp_path / "preserve.json"
        target.write_text('{"known": 1, "unknown_field": "keep_me"}')

        result = patch_json_file(target, lambda d: {**d, "known": 99})
        assert result["known"] == 99
        assert result["unknown_field"] == "keep_me"

    def test_replaces_existing_key(self, tmp_path):
        target = tmp_path / "replace.json"
        target.write_text('{"a": 1, "b": 2}')
        result = patch_json_file(target, lambda d: {**d, "a": 10})
        assert result["a"] == 10
        assert result["b"] == 2


class TestCreateBackup:
    def test_creates_backup_file(self, tmp_path):
        target = tmp_path / "data.txt"
        target.write_text("content")
        backup = create_backup(target)
        assert backup.exists()
        assert backup.read_text() == "content"

    def test_backup_has_timestamp_suffix(self, tmp_path):
        target = tmp_path / "data.txt"
        target.write_text("content")
        backup = create_backup(target)
        assert ".backup." in str(backup)

    def test_returns_original_when_missing(self, tmp_path):
        result = create_backup(tmp_path / "missing")
        assert result == tmp_path / "missing"


class TestWriteMarkdown:
    def test_writes_markdown(self, tmp_path):
        target = tmp_path / "SKILL.md"
        write_markdown(target, "# Title\nBody")
        assert target.read_text() == "# Title\nBody"
