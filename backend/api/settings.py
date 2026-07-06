"""Settings API endpoints — scoped settings CRUD via ``services.settings_service``.

Supported scopes: ``project``, ``global``, ``local``.
Internal / managed scopes are forbidden.
"""

from fastapi import APIRouter, HTTPException, Path

from services import settings_service

router = APIRouter()

ALLOWED_SCOPES = {"project", "global", "local"}
FORBIDDEN_SCOPES = {"internal", "managed"}


def _validate_scope(scope: str) -> None:
    """Validate scope and raise HTTPException if invalid."""
    if scope in FORBIDDEN_SCOPES:
        raise HTTPException(status_code=403, detail=f"Scope '{scope}' is not accessible")
    if scope not in ALLOWED_SCOPES:
        raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}")


@router.get("/{scope}")
async def get_settings(scope: str = Path(..., pattern="^(project|global|local)$")):
    """Read full settings for a given scope."""
    _validate_scope(scope)
    return await settings_service.get(scope)


@router.patch("/{scope}")
async def patch_settings(
    scope: str = Path(..., pattern="^(project|global|local)$"),
    update: dict = None,
):
    """Patch settings for a given scope (partial update)."""
    _validate_scope(scope)
    if not update:
        raise HTTPException(status_code=400, detail="Patch body is required")
    return await settings_service.patch(scope, update)
