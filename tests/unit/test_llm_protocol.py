"""
Tests for gtaa_validator.llm.protocol

Covers:
- TokenUsage: defaults, add(), total_tokens, estimated_cost_usd, to_dict(), __str__()
- LLMClientProtocol: runtime_checkable conformance for MockLLMClient and APILLMClient
"""

from unittest.mock import patch

import pytest

from gtaa_validator.llm.protocol import TokenUsage, LLMClientProtocol
from gtaa_validator.llm.client import MockLLMClient


# =========================================================================
# TokenUsage
# =========================================================================

class TestTokenUsageDefaults:
    """Tests for TokenUsage default state."""

    def test_all_fields_default_to_zero(self):
        """All fields start at 0."""
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_calls == 0
        assert usage.cost_per_million_input == 0.0
        assert usage.cost_per_million_output == 0.0


class TestTokenUsageAdd:
    """Tests for TokenUsage.add() method."""

    def test_add_increments_tokens_and_calls(self):
        """Single add() increments all counters."""
        usage = TokenUsage()
        usage.add(10, 20)
        assert usage.input_tokens == 10
        assert usage.output_tokens == 20
        assert usage.total_calls == 1

    def test_add_multiple_accumulates(self):
        """Multiple add() calls accumulate correctly."""
        usage = TokenUsage()
        usage.add(100, 50)
        usage.add(200, 100)
        usage.add(300, 150)
        assert usage.input_tokens == 600
        assert usage.output_tokens == 300
        assert usage.total_calls == 3


class TestTokenUsageTotalTokens:
    """Tests for TokenUsage.total_tokens property."""

    def test_total_tokens_is_sum(self):
        """total_tokens = input_tokens + output_tokens."""
        usage = TokenUsage(input_tokens=500, output_tokens=200)
        assert usage.total_tokens == 700

    def test_total_tokens_zero(self):
        """total_tokens is 0 when no tokens consumed."""
        usage = TokenUsage()
        assert usage.total_tokens == 0


class TestTokenUsageCost:
    """Tests for TokenUsage.estimated_cost_usd property."""

    def test_zero_pricing_returns_zero(self):
        """Zero cost_per_million yields $0.0."""
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        assert usage.estimated_cost_usd == 0.0

    def test_api_pricing_calculates_correctly(self):
        """Non-zero pricing produces correct cost estimate."""
        usage = TokenUsage(
            input_tokens=1_000_000,
            output_tokens=500_000,
            cost_per_million_input=0.075,
            cost_per_million_output=0.30,
        )
        # input: 1M * 0.075/1M = 0.075
        # output: 500K * 0.30/1M = 0.15
        assert usage.estimated_cost_usd == pytest.approx(0.225)


class TestTokenUsageToDict:
    """Tests for TokenUsage.to_dict() method."""

    def test_to_dict_keys(self):
        """to_dict() contains all expected keys."""
        usage = TokenUsage()
        d = usage.to_dict()
        expected_keys = {"input_tokens", "output_tokens", "total_tokens",
                         "total_calls", "estimated_cost_usd"}
        assert set(d.keys()) == expected_keys

    def test_to_dict_values_match_state(self):
        """to_dict() values reflect internal state."""
        usage = TokenUsage(input_tokens=100, output_tokens=50, total_calls=2)
        d = usage.to_dict()
        assert d["input_tokens"] == 100
        assert d["output_tokens"] == 50
        assert d["total_tokens"] == 150
        assert d["total_calls"] == 2
        assert d["estimated_cost_usd"] == 0.0

    def test_to_dict_rounds_cost(self):
        """to_dict() rounds estimated_cost_usd to 6 decimals."""
        usage = TokenUsage(
            input_tokens=1,
            cost_per_million_input=1.0,
        )
        d = usage.to_dict()
        assert d["estimated_cost_usd"] == 0.000001


class TestTokenUsageStr:
    """Tests for TokenUsage.__str__() method."""

    def test_str_mock_format(self):
        """Zero pricing shows mock format."""
        usage = TokenUsage(total_calls=3)
        s = str(usage)
        assert "Mock" in s
        assert "3 llamadas" in s
        assert "sin costo" in s

    def test_str_api_format(self):
        """Non-zero pricing shows cost format."""
        usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
            total_calls=2,
            cost_per_million_input=0.075,
            cost_per_million_output=0.30,
        )
        s = str(usage)
        assert "Tokens:" in s
        assert "Costo estimado:" in s
        assert "USD" in s


# =========================================================================
# LLMClientProtocol
# =========================================================================

class TestLLMClientProtocol:
    """Tests for LLMClientProtocol runtime_checkable conformance."""

    def test_mock_client_implements_protocol(self):
        """MockLLMClient is a structural subtype of LLMClientProtocol."""
        client = MockLLMClient()
        assert isinstance(client, LLMClientProtocol)

    @patch("gtaa_validator.llm.api_client.genai.Client")
    def test_api_client_implements_protocol(self, mock_genai):
        """APILLMClient is a structural subtype of LLMClientProtocol."""
        from gtaa_validator.llm.api_client import APILLMClient
        client = APILLMClient(api_key="test-key")
        assert isinstance(client, LLMClientProtocol)
