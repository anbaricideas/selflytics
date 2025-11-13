"""Cost tracking models for AI usage."""

from datetime import datetime

from pydantic import BaseModel


class ChatUsage(BaseModel):
    """Token usage for a single chat exchange."""

    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    reasoning_tokens: int = 0  # For o1 models
    cost_usd: float
    model: str
    timestamp: datetime


class TokenCost(BaseModel):
    """Token pricing for a model."""

    model: str
    input_cost_per_1m: float  # Cost per 1M input tokens
    output_cost_per_1m: float
    cached_cost_per_1m: float = 0.0
    reasoning_cost_per_1m: float = 0.0


# Pricing for gpt-4.1-mini (2025-04-14)
GPT_4_1_MINI_PRICING = TokenCost(
    model="gpt-4.1-mini-2025-04-14",
    input_cost_per_1m=0.15,
    output_cost_per_1m=0.60,
    cached_cost_per_1m=0.075,  # 50% discount for cached inputs
)
