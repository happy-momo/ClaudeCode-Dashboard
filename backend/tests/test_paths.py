"""Tests for path resolution utilities."""

import tempfile
from pathlib import Path

import pytest

from core.paths import resolve_safe_path


class TestResolveSafePath:
    @pytest.fixture
    def base_dir(self):
        """Create a temporary base directory."""
        d = Path(tempfile.mkdtemp()) / "base"
        d.mkdir()
        yield d
        # Cleanup
        import shutil
        shutil.rmtree(d.parent, ignore_errors=True)

    def test_allows_within_base(self, base_dir):
        result = resolve_safe_path(base_dir, "safe-skill.md")
        assert result.parent == base_dir.resolve()

    def test_detects_traversal(self, base_dir):
        with pytest.raises(ValueError, match="Path traversal"):
            resolve_safe_path(base_dir, "../etc/passwd")

    def test_detects_double_dot_outside(self, base_dir):
        with pytest.raises(ValueError, match="Path traversal"):
            resolve_safe_path(base_dir, "..")

    def test_handles_nested_safe_name(self, base_dir):
        """Even with nested segments in name, result must stay in base."""
        with pytest.raises(ValueError, match="Path traversal"):
            resolve_safe_path(base_dir, "subdir/../../etc/passwd")
