"""Tests for the Operation Planner decision logic."""

import pytest

from services.operation_planner import OperationPlanner


class TestOperationPlan:
    def test_skill_project_is_file(self):
        plan = OperationPlanner.plan("create", "skill", "my-skill", "project")
        assert plan.mode == "file"
        assert plan.risk_level == "low"

    def test_skill_global_is_file(self):
        plan = OperationPlanner.plan("update", "skill", "my-skill", "global")
        assert plan.mode == "file"

    def test_skill_plugin_is_readonly(self):
        plan = OperationPlanner.plan("update", "skill", "plugin-skill", "plugin")
        assert plan.mode == "readonly"

    def test_mcp_project_is_file(self):
        plan = OperationPlanner.plan("create", "mcp_server", "srv", "project")
        assert plan.mode == "file"

    def test_mcp_user_is_cli(self):
        plan = OperationPlanner.plan("create", "mcp_server", "srv", "user")
        assert plan.mode == "cli"

    def test_mcp_managed_is_readonly(self):
        plan = OperationPlanner.plan("update", "mcp_server", "srv", "managed")
        assert plan.mode == "readonly"

    def test_settings_project_is_file(self):
        plan = OperationPlanner.plan("patch", "settings", "s", "project")
        assert plan.mode == "file"

    def test_settings_local_is_file(self):
        plan = OperationPlanner.plan("patch", "settings", "s", "local")
        assert plan.mode == "file"

    def test_settings_user_is_file(self):
        plan = OperationPlanner.plan("patch", "settings", "s", "user")
        assert plan.mode == "file"

    def test_settings_managed_is_readonly(self):
        plan = OperationPlanner.plan("patch", "settings", "s", "managed")
        assert plan.mode == "readonly"

    def test_settings_internal_is_unsupported(self):
        plan = OperationPlanner.plan("patch", "settings", "s", "internal")
        assert plan.mode == "unsupported"
        assert plan.risk_level == "high"

    def test_plugin_install_is_cli(self):
        plan = OperationPlanner.plan("install", "plugin", "ref", "user")
        assert plan.mode == "cli"

    def test_plugin_uninstall_is_cli(self):
        plan = OperationPlanner.plan("uninstall", "plugin", "ref", "user")
        assert plan.mode == "cli"

    def test_plugin_enable_is_cli(self):
        plan = OperationPlanner.plan("enable", "plugin", "ref", "user")
        assert plan.mode == "cli"

    def test_plugin_disable_is_cli(self):
        plan = OperationPlanner.plan("disable", "plugin", "ref", "user")
        assert plan.mode == "cli"

    def test_plugin_move_scope_is_cli(self):
        plan = OperationPlanner.plan("move_scope", "plugin", "ref", "user")
        assert plan.mode == "cli"

    def test_plugin_cache_is_readonly(self):
        plan = OperationPlanner.plan("update", "plugin_cache", "cache", "user")
        assert plan.mode == "readonly"

    def test_managed_is_readonly(self):
        plan = OperationPlanner.plan("update", "managed", "policy", "user")
        assert plan.mode == "readonly"

    def test_unknown_resource_is_unsupported(self):
        plan = OperationPlanner.plan("delete", "unknown_resource", "x", "project")
        assert plan.mode == "unsupported"

    def test_plan_has_reason(self):
        plan = OperationPlanner.plan("create", "skill", "s", "project")
        assert len(plan.reason) > 0

    def test_plan_has_warnings_empty_by_default(self):
        plan = OperationPlanner.plan("create", "skill", "s", "project")
        assert plan.warnings == []
