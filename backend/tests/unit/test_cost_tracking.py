"""Tests for cost tracking utilities."""

from datetime import UTC, datetime

import pytest

from app.models.cost_tracking import GPT_4_1_MINI_PRICING, ChatUsage, TokenCost
from app.utils.cost_tracking import calculate_cost, create_usage_record


class TestTokenCost:
    """Test TokenCost model."""

    def test_gpt_4_1_mini_pricing(self):
        """Test GPT-4.1-mini pricing constants."""
        assert GPT_4_1_MINI_PRICING.model == "gpt-4.1-mini-2025-04-14"
        assert GPT_4_1_MINI_PRICING.input_cost_per_1m == 0.15
        assert GPT_4_1_MINI_PRICING.output_cost_per_1m == 0.60
        assert GPT_4_1_MINI_PRICING.cached_cost_per_1m == 0.075


class TestChatUsage:
    """Test ChatUsage model."""

    def test_valid_chat_usage(self):
        """Test creating valid ChatUsage record."""
        now = datetime.now(UTC)
        usage = ChatUsage(
            input_tokens=100,
            output_tokens=200,
            cached_tokens=50,
            reasoning_tokens=0,
            cost_usd=0.0001,
            model="gpt-4.1-mini-2025-04-14",
            timestamp=now,
        )

        assert usage.input_tokens == 100
        assert usage.output_tokens == 200
        assert usage.cached_tokens == 50
        assert usage.reasoning_tokens == 0
        assert usage.cost_usd == 0.0001
        assert usage.model == "gpt-4.1-mini-2025-04-14"
        assert usage.timestamp == now


class TestCalculateCost:
    """Test cost calculation function."""

    def test_calculate_basic_cost(self):
        """Test basic cost calculation with no cached/reasoning tokens."""
        # 1000 input tokens, 2000 output tokens
        # Cost = (1000 * 0.15 / 1M) + (2000 * 0.60 / 1M)
        # Cost = 0.00015 + 0.0012 = 0.00135
        cost = calculate_cost(input_tokens=1000, output_tokens=2000)

        assert cost == pytest.approx(0.00135, rel=1e-5)

    def test_calculate_cost_with_cached_tokens(self):
        """Test cost calculation with cached tokens (50% discount)."""
        # 1000 input tokens, 500 cached tokens, 2000 output tokens
        # Cost = (1000 * 0.15 / 1M) + (500 * 0.075 / 1M) + (2000 * 0.60 / 1M)
        # Cost = 0.00015 + 0.0000375 + 0.0012 = 0.0013875
        cost = calculate_cost(input_tokens=1000, output_tokens=2000, cached_tokens=500)

        assert cost == pytest.approx(0.0013875, rel=1e-5)

    def test_calculate_cost_with_reasoning_tokens(self):
        """Test cost calculation with reasoning tokens (o1 models)."""
        # Create custom pricing with reasoning tokens
        pricing = TokenCost(
            model="o1-preview",
            input_cost_per_1m=15.0,
            output_cost_per_1m=60.0,
            reasoning_cost_per_1m=30.0,
        )

        # 100 input, 200 output, 300 reasoning
        # Cost = (100 * 15 / 1M) + (200 * 60 / 1M) + (300 * 30 / 1M)
        # Cost = 0.0015 + 0.012 + 0.009 = 0.0225
        cost = calculate_cost(
            input_tokens=100,
            output_tokens=200,
            reasoning_tokens=300,
            pricing=pricing,
        )

        assert cost == pytest.approx(0.0225, rel=1e-5)

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        cost = calculate_cost(input_tokens=0, output_tokens=0)
        assert cost == 0.0

    def test_calculate_cost_typical_conversation(self):
        """Test cost for typical conversation turn."""
        # Typical: 500 input, 300 output
        # Cost = (500 * 0.15 / 1M) + (300 * 0.60 / 1M)
        # Cost = 0.000075 + 0.00018 = 0.000255
        cost = calculate_cost(input_tokens=500, output_tokens=300)

        assert cost == pytest.approx(0.000255, rel=1e-5)
        assert cost < 0.001  # Less than $0.001 per turn


class TestCreateUsageRecord:
    """Test usage record creation from API response."""

    def test_create_usage_record_basic(self):
        """Test creating usage record from API response."""
        usage_dict = {"prompt_tokens": 1000, "completion_tokens": 2000}

        record = create_usage_record(usage_dict)

        assert record.input_tokens == 1000
        assert record.output_tokens == 2000
        assert record.cached_tokens == 0
        assert record.model == "gpt-4.1-mini-2025-04-14"
        assert record.cost_usd == pytest.approx(0.00135, rel=1e-5)
        assert isinstance(record.timestamp, datetime)

    def test_create_usage_record_with_cached_tokens(self):
        """Test creating usage record with cached tokens."""
        usage_dict = {
            "prompt_tokens": 1000,
            "completion_tokens": 2000,
            "prompt_tokens_details": {"cached_tokens": 500},
        }

        record = create_usage_record(usage_dict)

        assert record.input_tokens == 1000
        assert record.output_tokens == 2000
        assert record.cached_tokens == 500
        # Cost calculation:
        # - Total prompt tokens: 1000
        # - Cached tokens: 500
        # - Non-cached input: 1000 - 500 = 500
        # Cost = (500 * 0.15 / 1M) + (500 * 0.075 / 1M) + (2000 * 0.60 / 1M)
        # Cost = 0.000075 + 0.0000375 + 0.0012 = 0.0013125
        assert record.cost_usd == pytest.approx(0.0013125, rel=1e-5)

    def test_create_usage_record_missing_fields(self):
        """Test creating usage record with missing fields (defaults to 0)."""
        usage_dict = {}

        record = create_usage_record(usage_dict)

        assert record.input_tokens == 0
        assert record.output_tokens == 0
        assert record.cached_tokens == 0
        assert record.cost_usd == 0.0

    def test_create_usage_record_custom_model(self):
        """Test creating usage record with custom model."""
        usage_dict = {"prompt_tokens": 100, "completion_tokens": 200}

        record = create_usage_record(usage_dict, model="gpt-4o")

        assert record.model == "gpt-4o"
