"""Claude CLI status API."""

from fastapi import APIRouter, HTTPException

from services import claude_cli_service

router = APIRouter()


@router.get("/status")
async def get_claude_status():
    """Get Claude CLI installation status and version."""
    cli = claude_cli_service.ClaudeCLIService()
    installed = cli.check_installed()

    result = {
        "installed": installed,
        "version": None,
        "path": None,
        "warnings": [],
    }

    if installed:
        result["version"] = cli.get_version()
        # Use the same resolution method as the service (handles Windows .CMD)
        cli_path = cli._resolve_cli_path()
        if cli_path:
            result["path"] = cli_path
    else:
        result["warnings"].append(
            "Claude Code CLI is not installed. "
            "Install it with: npm install -g @anthropic-ai/claude-code"
        )

    return result


@router.post("/run-plan")
async def run_plan(operation: str, resource_type: str, target: str, scope: str = "project"):
    """Debug endpoint to test operation planning.

    Returns the OperationPlan for the given parameters without executing it.
    """
    from services.operation_planner import OperationPlanner

    plan = OperationPlanner.plan(operation, resource_type, target, scope)

    return {
        "operation": plan.operation,
        "resource_type": plan.resource_type,
        "target": plan.target,
        "mode": plan.mode,
        "reason": plan.reason,
        "risk_level": plan.risk_level,
        "requires_restart": plan.requires_restart,
        "requires_reload_plugins": plan.requires_reload_plugins,
        "warnings": plan.warnings,
        "confirmation_required": plan.confirmation_required,
    }
