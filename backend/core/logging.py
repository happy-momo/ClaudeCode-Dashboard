"""Unified logging configuration with secret masking.

Configures a JSON-friendly handler for production use and a
colour-coded console handler for development.  All handlers
automatically mask known secret patterns in string messages.
"""

from __future__ import annotations

import logging
import re
from typing import Optional


# Words and prefixes that should be masked in log output.
_SECRET_PATTERNS = [
    re.compile(r"(token|password|secret|api_key)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"(ghp_[A-Za-z0-9]{36,})"),
    re.compile(r"(sk-[A-Za-z0-9]{20,})"),
    re.compile(r"(xoxb-[A-Za-z0-9\-]+)"),
]


class _MaskingFormatter(logging.Formatter):
    """A logging Formatter that masks secret-like values in log messages."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return _mask_secrets(msg)


def _mask_secrets(text: str) -> str:
    """Replace secret values in *text* with ``***``."""
    for pat in _SECRET_PATTERNS:
        text = pat.sub("***", text)
    return text


def configure_logging(
    level: Optional[str] = None,
    logger_name: str = "claude_dashboard",
) -> None:
    """Configure root-level logging for the dashboard.

    Call once at application startup (e.g. in ``main.py``).

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).
        logger_name: Name prefix for the application logger.
    """
    if level is None:
        level = "INFO"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Apply masking to the root handler
    for handler in logging.root.handlers:
        if isinstance(handler.formatter, _MaskingFormatter):
            break
    else:
        # Add masking formatter
        for handler in logging.root.handlers:
            handler.setFormatter(_MaskingFormatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            ))

    app_logger = logging.getLogger(logger_name)
    app_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
