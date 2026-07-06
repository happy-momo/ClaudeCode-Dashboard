"""Token counting utilities using Anthropic's official tokenizer"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import the official tokenizer, fall back to heuristic if unavailable
try:
    from anthropic_tokenizer import count_tokens as anthropic_count_tokens
    HAS_OFFICIAL_TOKENIZER = True
except ImportError:
    HAS_OFFICIAL_TOKENIZER = False
    logger.warning("anthropic-tokenizer not installed. Using heuristic estimation.")


def estimate_tokens_heuristic(text: str) -> int:
    """Estimate token count from text using heuristic.

    Uses a simple heuristic: ~1 token per 4 characters.
    This is less accurate than the official tokenizer.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_tokens(text: str) -> int:
    """Calculate token count for text.

    Uses Anthropic's official tokenizer if available, otherwise falls back
    to heuristic estimation (~1 token per 4 characters).
    """
    if not text:
        return 0

    if HAS_OFFICIAL_TOKENIZER:
        try:
            return anthropic_count_tokens(text)
        except Exception as e:
            # Fall back to heuristic if tokenizer fails
            logger.warning("Tokenizer error: %s. Using heuristic estimation.", e)
            return estimate_tokens_heuristic(text)

    return estimate_tokens_heuristic(text)


def calculate_text_tokens(text: str) -> int:
    """Calculate token count for text.

    Uses Anthropic's official tokenizer for accurate counts matching
    Claude's actual token usage.
    """
    return estimate_tokens(text)
