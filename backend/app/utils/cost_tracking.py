"""Cost calculation utilities."""

from datetime import UTC, datetime

from app.models.cost_tracking import GPT_4_1_MINI_PRICING, ChatUsage, TokenCost


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


def create_usage_record(usage_dict: dict, model: str = "gpt-4.1-mini-2025-04-14") -> ChatUsage:
    """
    Create ChatUsage record from API response.

    Args:
        usage_dict: Usage dictionary from OpenAI API response
        model: Model name

    Returns:
        ChatUsage record with calculated cost
    """
    input_tokens = usage_dict.get("prompt_tokens", 0)
    output_tokens = usage_dict.get("completion_tokens", 0)
    cached_tokens = usage_dict.get("prompt_tokens_details", {}).get("cached_tokens", 0)

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
