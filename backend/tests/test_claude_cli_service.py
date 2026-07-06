"""Tests for Claude CLI service (mocked)."""

import asyncio
import shutil
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.errors import CliNotFoundError
from services.claude_cli_service import ClaudeCLIService, CliResult


class TestCliResult:
    def test_ok_when_zero(self):
        r = CliResult(exit_code=0)
        assert r.ok is True

    def test_not_ok_when_nonzero(self):
        r = CliResult(exit_code=1)
        assert r.ok is False


class TestClaudeCLIServiceCheckInstalled:
    def test_installed_when_in_path(self):
        with patch("shutil.which", return_value="/usr/bin/claude"):
            svc = ClaudeCLIService()
            assert svc.check_installed() is True

    def test_not_installed_when_not_in_path(self):
        with patch("shutil.which", return_value=None):
            svc = ClaudeCLIService()
            assert svc.check_installed() is False


class TestClaudeCLIServiceResolvePath:
    """Tests for _resolve_cli_path — the Windows-compatible path resolver."""

    def test_returns_path_when_found(self):
        with patch("shutil.which", return_value="/usr/bin/claude"):
            svc = ClaudeCLIService()
            assert svc._resolve_cli_path() == "/usr/bin/claude"

    def test_returns_none_when_not_found(self):
        with patch("shutil.which", return_value=None):
            svc = ClaudeCLIService()
            assert svc._resolve_cli_path() is None

    def test_returns_cmd_path_on_windows(self):
        """On Windows, shutil.which may return a .CMD wrapper path."""
        with patch("shutil.which", return_value=r"D:\nodejs\claude.CMD"):
            svc = ClaudeCLIService()
            assert svc._resolve_cli_path() == r"D:\nodejs\claude.CMD"


class TestClaudeCLIServiceGetVersion:
    def test_returns_version_on_success(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="version 1.2.3\n")
                svc = ClaudeCLIService()
                assert svc.get_version() == "version 1.2.3"

    def test_returns_none_on_failure(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)
                svc = ClaudeCLIService()
                assert svc.get_version() is None

    def test_returns_none_when_not_installed(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value=None):
            svc = ClaudeCLIService()
            assert svc.get_version() is None


class TestClaudeCLIServiceRun:
    def test_raises_when_not_installed(self):
        svc = ClaudeCLIService()
        with patch.object(svc, "_resolve_cli_path", return_value=None):
            with pytest.raises(CliNotFoundError):
                svc.run(["--version"])

    def test_returns_structured_result(self):
        svc = ClaudeCLIService()
        with patch.object(svc, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="out\n", stderr="err\n"
                )
                result = svc.run(["--version"])
                assert result.exit_code == 0
                assert result.stdout == "out\n"
                assert result.stderr == "err\n"

    def test_uses_resolved_path_in_subprocess(self):
        """Verify that subprocess.run receives the resolved path, not the bare name."""
        resolved = r"D:\nodejs\claude.CMD"
        svc = ClaudeCLIService()
        with patch.object(svc, "_resolve_cli_path", return_value=resolved):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                svc.run(["--version"])
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == resolved  # full path, not "claude"


class TestClaudeCLIServicePluginMethods:
    def test_plugin_install_builds_correct_args(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_install("my-plugin@official", "project", "/some/project")
                args = mock_run.call_args[0][0]
                assert "plugin" in args
                assert "install" in args
                assert "my-plugin@official" in args
                assert "--scope" in args
                assert "project" in args
                # project_root is passed as cwd, not as --project flag
                assert "--project" not in args
                assert mock_run.call_args[1].get("cwd") == "/some/project"

    def test_plugin_uninstall_builds_correct_args(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_uninstall("my-plugin", "user")
                args = mock_run.call_args[0][0]
                assert "uninstall" in args

    def test_plugin_uninstall_passes_project_root_as_cwd(self):
        """project_root is passed as cwd to subprocess.run."""
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_uninstall("my-plugin", "project", "/some/project")
                assert mock_run.call_args[1].get("cwd") == "/some/project"

    def test_plugin_enable_builds_correct_args(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_enable("my-plugin")
                args = mock_run.call_args[0][0]
                assert "enable" in args

    def test_plugin_enable_passes_project_root_as_cwd(self):
        """project_root is passed as cwd to subprocess.run."""
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_enable("my-plugin", "project", "/some/project")
                args = mock_run.call_args[0][0]
                assert "enable" in args
                assert "--scope" in args
                assert "project" in args
                assert mock_run.call_args[1].get("cwd") == "/some/project"

    def test_plugin_disable_builds_correct_args(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_disable("my-plugin")
                args = mock_run.call_args[0][0]
                assert "disable" in args

    def test_plugin_disable_passes_project_root_as_cwd(self):
        """project_root is passed as cwd to subprocess.run."""
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_disable("my-plugin", "project", "/some/project")
                args = mock_run.call_args[0][0]
                assert "disable" in args
                assert "--scope" in args
                assert "project" in args
                assert mock_run.call_args[1].get("cwd") == "/some/project"

    def test_plugin_list_builds_correct_args(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_list()
                args = mock_run.call_args[0][0]
                assert "list" in args
                assert "--json" in args
                # No --project flag (CLI doesn't support it; uses cwd instead)
                assert "--project" not in args

    def test_plugin_list_passes_project_root_as_cwd(self):
        """project_root is passed as cwd to subprocess.run, not as --project."""
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.plugin_list(project_root="/some/project")
                args = mock_run.call_args[0][0]
                assert "--project" not in args
                assert mock_run.call_args[1].get("cwd") == "/some/project"

    def test_marketplace_list_builds_correct_args(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.marketplace_list()
                args = mock_run.call_args[0][0]
                assert "marketplace" in args
                assert "list" in args

    def test_marketplace_add_builds_correct_args(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.marketplace_add("https://example.com")
                args = mock_run.call_args[0][0]
                assert "add" in args

    def test_marketplace_update_builds_correct_args(self):
        with patch.object(ClaudeCLIService, "_resolve_cli_path", return_value="/usr/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                svc = ClaudeCLIService()
                svc.marketplace_update()
                args = mock_run.call_args[0][0]
                assert "update" in args


class TestClaudeCLIServiceNotInstalled:
    def test_plugin_install_raises_when_not_installed(self):
        svc = ClaudeCLIService()
        with patch.object(svc, "_resolve_cli_path", return_value=None):
            with pytest.raises(CliNotFoundError):
                svc.plugin_install("ref", "user")


class TestIsAlreadyInState:
    """Tests for the _is_already_in_state idempotency helper."""

    def test_already_enabled(self):
        from services.plugin_service import _is_already_in_state
        assert _is_already_in_state("Plugin is already enabled at project scope", "enable") is True

    def test_already_disabled(self):
        from services.plugin_service import _is_already_in_state
        assert _is_already_in_state("Plugin is already disabled at project scope", "disable") is True

    def test_not_already_state(self):
        from services.plugin_service import _is_already_in_state
        assert _is_already_in_state("Some other error", "enable") is False

    def test_empty_stderr(self):
        from services.plugin_service import _is_already_in_state
        assert _is_already_in_state("", "enable") is False

    def test_wrong_action(self):
        from services.plugin_service import _is_already_in_state
        assert _is_already_in_state("Plugin is already enabled", "disable") is False
