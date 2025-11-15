"""Cost calculation utilities."""

from datetime import UTC, datetime
from typing import Any

from app.models.cost_tracking import (
    GPT_4_1_MINI_MODEL,
    GPT_4_1_MINI_PRICING,
    ChatUsage,
    TokenCost,
)


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
    reasoning_tokens: int = 0,
    pricing: TokenCost = GPT_4_1_MINI_PRICING,
) -> float:
    """
    Calculate cost in USD for token usage.

    Args:
        input_tokens: Non-cached input tokens
        output_tokens: Output tokens
        cached_tokens: Cached input tokens (discounted)
        reasoning_tokens: Reasoning tokens (o1 models)
        pricing: Token pricing model

    Returns:
        Total cost in USD
    """
    return (
        (input_tokens * pricing.input_cost_per_1m / 1_000_000)
        + (output_tokens * pricing.output_cost_per_1m / 1_000_000)
        + (cached_tokens * pricing.cached_cost_per_1m / 1_000_000)
        + (reasoning_tokens * pricing.reasoning_cost_per_1m / 1_000_000)
    )


def create_usage_record(usage_obj: Any, model: str = GPT_4_1_MINI_MODEL) -> ChatUsage:
    """
    Create ChatUsage record from Pydantic-AI RunUsage object or dict.

    Args:
        usage_obj: RunUsage object from Pydantic-AI (or dict for backwards compat)
        model: Model name

    Returns:
        ChatUsage record with calculated cost
    """
    # Handle both RunUsage objects and dict (backwards compatibility)
    if hasattr(usage_obj, "input_tokens"):
        # RunUsage object from Pydantic-AI
        input_tokens = usage_obj.input_tokens or 0
        output_tokens = usage_obj.output_tokens or 0
        # Check for cached_input_tokens attribute
        cached_tokens = getattr(usage_obj, "cached_input_tokens", 0) or 0
    else:
        # Legacy dict format
        input_tokens = usage_obj.get("prompt_tokens", 0)
        output_tokens = usage_obj.get("completion_tokens", 0)
        cached_tokens = usage_obj.get("prompt_tokens_details", {}).get("cached_tokens", 0)

    cost = calculate_cost(
        input_tokens=input_tokens - cached_tokens,  # Non-cached input
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
    )

    return ChatUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        cost_usd=cost,
        model=model,
        timestamp=datetime.now(UTC),
    )
