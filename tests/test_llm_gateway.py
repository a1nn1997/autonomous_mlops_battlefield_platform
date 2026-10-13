import pytest
import asyncio
from unittest.mock import MagicMock, patch
import httpx

from src.llm_gateway import (
    LLMGateway,
    GeminiProvider,
    DeterministicFallbackProvider,
    LLMProviderFactory
)

@pytest.mark.asyncio
async def test_vertex_ai_success():
    # 1. Test GeminiProvider configured for Google Cloud Vertex AI
    provider = GeminiProvider(
        project="test-gcp-project-123",
        location="us-central1",
        use_vertex=True
    )
    assert provider.provider_name == "Google Cloud Vertex AI"
    assert provider.has_valid_key is True

    # Mock the google.genai Client response
    mock_response = MagicMock()
    mock_response.text = "Vertex AI operational summary: WAPE stable at 13.00% across multi-store demand."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(provider, "_get_client", return_value=mock_client):
        result = await provider.generate(
            messages=[{"role": "user", "content": "Summarize operational forecast status"}],
            system_prompt="You are an autonomous MLOps platform assistant."
        )

        assert result["status"] == "SUCCESS"
        assert result["provider"] == "Google Cloud Vertex AI"
        assert "Vertex AI operational summary" in result["text"]
        assert result["latency_ms"] >= 0.0

@pytest.mark.asyncio
async def test_llm_gateway_timeout_handling():
    gateway = LLMGateway()

    # Mock active_provider to simulate a network or API timeout
    mock_provider = MagicMock()
    mock_provider.has_valid_key = True
    mock_provider.provider_name = "Mocked Vendor"
    mock_provider.model_name = "mock-model"
    mock_provider.generate = MagicMock(side_effect=asyncio.TimeoutError("Upstream API call exceeded SLA threshold"))

    with patch.object(gateway, "active_provider", mock_provider):
        with patch.object(gateway, "_load_config"):
            res = await gateway.generate_response(
                messages=[{"role": "user", "content": "Trigger timeout test"}]
            )

            assert res["status"] == "FAILED"
            assert "timed out or failed" in res["error"]
            assert res["text"] is None
            assert res["latency_ms"] >= 0.0

@pytest.mark.asyncio
async def test_missing_credentials_fallback():
    # 1. When credentials are completely missing, has_valid_key is False
    provider = GeminiProvider(api_key=None, project=None, use_vertex=False)
    assert provider.has_valid_key is False

    gateway = LLMGateway()
    mock_no_key_provider = MagicMock()
    mock_no_key_provider.has_valid_key = False
    mock_no_key_provider.provider_name = "Google Gemini"
    mock_no_key_provider.model_name = "gemini-2.5-flash"

    with patch.object(gateway, "active_provider", mock_no_key_provider):
        with patch.object(gateway, "_load_config"):
            res = await gateway.generate_response(
                messages=[{"role": "user", "content": "Status update"}]
            )
            assert res["status"] == "NO_API_KEY"
            assert res["text"] is None
            assert "No API key provided" in res["error"]

    # 2. DeterministicFallbackProvider guarantees 100% availability
    fallback_provider = DeterministicFallbackProvider()
    assert fallback_provider.has_valid_key is True
    assert fallback_provider.provider_name == "Deterministic Fallback"

    fallback_res = await fallback_provider.generate(
        messages=[{"role": "user", "content": "Status update"}]
    )
    assert fallback_res["status"] == "FALLBACK"
    assert "Deterministic fallback active" in fallback_res["text"]
    assert fallback_res["latency_ms"] < 10.0
