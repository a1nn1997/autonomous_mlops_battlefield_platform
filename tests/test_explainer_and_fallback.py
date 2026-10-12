import pytest
from src.explainer.fallback import RuleBasedExplainerFallback
from src.explainer.golden_set import get_golden_set
from src.explainer.benchmark import ExplainerBenchmark

def test_rule_based_explainer_fallback():
    fallback = RuleBasedExplainerFallback()
    context = {
        "incident_type": "PRICE_DRIFT_ALERT",
        "metrics": {"wape": 0.35, "bias": 0.20, "baseline_wape": 0.18},
        "drift_report": {
            "max_psi": 0.42,
            "features": {
                "sell_price": {"psi": 0.42, "status": "CRITICAL_DRIFT", "baseline_mean": 3.5, "current_mean": 5.6}
            }
        },
        "decay_report": {"current_wape": 0.35, "relative_decay": 0.94}
    }

    result = fallback.explain(context)
    assert result["success"] is True
    assert result["source"] == "RULE_BASED_FALLBACK"
    assert "0.42" in result["explanation"]
    assert "35.00%" in result["explanation"]
    assert len(result["cited_metrics"]) >= 3

def test_golden_set_size():
    cases = get_golden_set()
    # Requirements specify a golden set of 30+ cases
    assert len(cases) >= 30
    for case in cases:
        assert "case_id" in case
        assert "context" in case
        assert "expected_citations" in case
        assert "ground_truth_root_cause" in case

def test_explainer_benchmark():
    benchmark = ExplainerBenchmark()
    # Run on sample of 4 cases for fast unit test
    results = benchmark.run_benchmark(sample_size=4)
    assert "summary_table" in results
    assert len(results["summary_table"]) == 2

@pytest.mark.asyncio
async def test_vertex_ai_adapter_and_fallback():
    from src.llm_gateway import GeminiProvider
    from unittest.mock import MagicMock, patch

    # 1. Test fallback when no credentials/keys exist
    provider = GeminiProvider(api_key=None, project=None, use_vertex=False)
    assert provider.model_name == "gemini-2.5-flash"
    assert provider.has_valid_key is False
    res = await provider.generate([{"role": "user", "content": "hello"}])
    assert res["status"] in ("ERROR", "FALLBACK")

    # 2. Test Vertex AI client with mocked google.genai Client
    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Vertex AI generated response"
        mock_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_instance

        vertex_provider = GeminiProvider(project="test-project", location="us-central1", use_vertex=True)
        assert vertex_provider.provider_name == "Google Cloud Vertex AI"
        assert vertex_provider.has_valid_key is True

        gen_res = await vertex_provider.generate([{"role": "user", "content": "analyze drift"}])
        assert gen_res["status"] == "SUCCESS"
        assert gen_res["text"] == "Vertex AI generated response"
        assert gen_res["provider"] == "Google Cloud Vertex AI"
