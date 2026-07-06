"""Structured error handling for the Claude Dashboard API.

Provides a centralized error model, error code registry, and FastAPI exception
handlers so that *all* API errors return a consistent JSON shape instead of
raw Python tracebacks.
"""

from __future__ import annotations

import logging
import traceback
from enum import Enum
from typing import Any, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------

class ErrorCodes(str, Enum):
    CLAUDE_CLI_NOT_FOUND = "CLAUDE_CLI_NOT_FOUND"
    CLAUDE_CLI_COMMAND_FAILED = "CLAUDE_CLI_COMMAND_FAILED"
    INVALID_PROJECT_ROOT = "INVALID_PROJECT_ROOT"
    INVALID_SCOPE = "INVALID_SCOPE"
    INVALID_RESOURCE_NAME = "INVALID_RESOURCE_NAME"
    PATH_TRAVERSAL_DETECTED = "PATH_TRAVERSAL_DETECTED"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    YAML_FRONTMATTER_ERROR = "YAML_FRONTMATTER_ERROR"
    OPERATION_UNSUPPORTED = "OPERATION_UNSUPPORTED"
    READONLY_RESOURCE = "READONLY_RESOURCE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SECRET_DETECTED = "SECRET_DETECTED"
    RISKY_COMMAND = "RISKY_COMMAND"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Structured error response returned to the client."""
    code: str
    message: str
    details: Optional[dict[str, Any]] = None
    warnings: list[str] = []


class ApiError(Exception):
    """Base exception for all API-level errors.

    Subclasses can override default_code, default_message, status_code and
    recoverable to tailor the response.
    """

    default_code: str = "INTERNAL_ERROR"
    default_message: str = "An unexpected error occurred."
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    recoverable: bool = False

    def __init__(
        self,
        code: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        warnings: Optional[list[str]] = None,
    ):
        self.code = code or self.default_code
        self.message = message or self.default_message
        self.details = details or {}
        self.warnings = warnings or []
        super().__init__(f"{self.code}: {self.message}")


# --- Concrete error types --------------------------------------------------

class CliNotFoundError(ApiError):
    default_code = ErrorCodes.CLAUDE_CLI_NOT_FOUND
    default_message = "Claude Code CLI is not installed or not in PATH."
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    recoverable = True


class CommandFailedError(ApiError):
    default_code = ErrorCodes.CLAUDE_CLI_COMMAND_FAILED
    default_message = "CLI command failed."
    recoverable = True


class InvalidProjectRootError(ApiError):
    default_code = ErrorCodes.INVALID_PROJECT_ROOT
    default_message = "The provided projectRoot is invalid or does not point to a directory."
    status_code = status.HTTP_400_BAD_REQUEST
    recoverable = True


class InvalidScopeError(ApiError):
    default_code = ErrorCodes.INVALID_SCOPE
    default_message = "The requested scope is not supported."
    status_code = status.HTTP_400_BAD_REQUEST
    recoverable = True


class InvalidResourceNameError(ApiError):
    default_code = ErrorCodes.INVALID_RESOURCE_NAME
    default_message = "The resource name is invalid."
    status_code = status.HTTP_400_BAD_REQUEST
    recoverable = True


class PathTraversalError(ApiError):
    default_code = ErrorCodes.PATH_TRAVERSAL_DETECTED
    default_message = "Path traversal detected — the requested path escapes the allowed directory."
    status_code = status.HTTP_403_FORBIDDEN
    recoverable = False


class FileNotFoundError(ApiError):
    default_code = ErrorCodes.FILE_NOT_FOUND
    default_message = "The requested file or resource was not found."
    status_code = status.HTTP_404_NOT_FOUND
    recoverable = True


class JsonParseError(ApiError):
    default_code = ErrorCodes.JSON_PARSE_ERROR
    default_message = "Failed to parse JSON file."
    status_code = status.HTTP_400_BAD_REQUEST
    recoverable = True


class YamlFrontmatterError(ApiError):
    default_code = ErrorCodes.YAML_FRONTMATTER_ERROR
    default_message = "YAML frontmatter is invalid."
    status_code = status.HTTP_400_BAD_REQUEST
    recoverable = True


class OperationUnsupportedError(ApiError):
    default_code = ErrorCodes.OPERATION_UNSUPPORTED
    default_message = "This operation is not supported in the current environment."
    status_code = status.HTTP_501_NOT_IMPLEMENTED
    recoverable = True


class ReadonlyResourceError(ApiError):
    default_code = ErrorCodes.READONLY_RESOURCE
    default_message = "This resource is read-only and cannot be modified."
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    recoverable = False


class PermissionDeniedError(ApiError):
    default_code = ErrorCodes.PERMISSION_DENIED
    default_message = "Insufficient permissions to perform this operation."
    status_code = status.HTTP_403_FORBIDDEN
    recoverable = False


class SecretDetectedError(ApiError):
    default_code = ErrorCodes.SECRET_DETECTED
    default_message = "Potential secret detected in the request data."
    status_code = status.HTTP_400_BAD_REQUEST
    recoverable = True


class RiskyCommandError(ApiError):
    default_code = ErrorCodes.RISKY_COMMAND
    default_message = "Potentially dangerous command detected."
    status_code = status.HTTP_400_BAD_REQUEST
    recoverable = True


class PartialSuccessError(ApiError):
    default_code = ErrorCodes.PARTIAL_SUCCESS
    default_message = "The operation completed partially."
    status_code = status.HTTP_207_MULTI_STATUS
    recoverable = True


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

def register_exception_handlers(app) -> None:  # noqa: C901
    """Register global exception handlers on a FastAPI *app* instance.

    Must be called *before* any route decorators (or during startup).
    """

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        # Log the full traceback internally (sanitized).
        logger.error(
            "ApiError [%s] %s | %s %s",
            exc.code,
            exc.message,
            request.method,
            request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=exc.code,
                message=exc.message,
                details=exc.details if exc.details else None,
                warnings=exc.warnings,
            ).model_dump(),
        )

    @app.exception_handler(ValueError)
    @app.exception_handler(TypeError)
    async def value_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Value/Type error: %s | %s %s", exc, request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                code="INVALID_REQUEST",
                message=str(exc),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # NEVER expose Python tracebacks to the client.
        logger.error(
            "Unhandled exception: %s\n%s | %s %s",
            type(exc).__name__,
            traceback.format_exc(),
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code="INTERNAL_ERROR",
                message="An unexpected internal error occurred.",
            ).model_dump(),
        )
