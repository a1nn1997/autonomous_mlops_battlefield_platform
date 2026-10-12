import pytest
import shutil
from pathlib import Path
from starlette.testclient import TestClient
from src.models.registry import ModelRegistry
from src.models.lightgbm_model import LightGBMForecaster
from src.data.dataset import generate_retail_data
from src.data.features import FeaturePipeline
from src.serving.app import app, load_active_model

@pytest.fixture
def temp_registry(tmp_path):
    reg = ModelRegistry(registry_dir=tmp_path / "registry")
    return reg

@pytest.fixture
def client():
    load_active_model()
    import src.serving.app as serving_module
    if serving_module.active_model is None:
        raw_df = generate_retail_data(n_items=2, n_stores=1, start_date="2024-01-01", end_date="2024-03-31")
        pipeline = FeaturePipeline()
        feat_df = pipeline.fit_transform(raw_df)
        m = LightGBMForecaster(params={"n_estimators": 10, "verbose": -1})
        m.fit(feat_df)
        serving_module.registry.register("v1", m, {"wape": 0.1325}, description="Fixture v1", promote=True)
        load_active_model()
    return TestClient(app)

def test_model_registry_and_rollback(temp_registry):
    raw_df = generate_retail_data(n_items=2, n_stores=1, start_date="2023-01-01", end_date="2023-03-31")
    pipeline = FeaturePipeline()
    feat_df = pipeline.fit_transform(raw_df)

    m1 = LightGBMForecaster(params={"n_estimators": 20, "verbose": -1})
    m1.fit(feat_df)
    temp_registry.register("v1", m1, {"wape": 0.25}, description="Initial v1", promote=True)
    assert temp_registry.get_champion()[0] == "v1"

    m2 = LightGBMForecaster(params={"n_estimators": 20, "verbose": -1})
    m2.fit(feat_df)
    temp_registry.register("v2", m2, {"wape": 0.22}, description="Improved v2", promote=True)
    assert temp_registry.get_champion()[0] == "v2"

    # Rollback to v1
    new_active, old_active = temp_registry.rollback()
    assert new_active == "v1"
    assert old_active == "v2"
    assert temp_registry.get_champion()[0] == "v1"

def test_fastapi_health_and_models(client):
    # Health endpoint
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "model_version" in data

    # Models list
    resp = client.get("/models")
    assert resp.status_code == 200
    assert "models" in resp.json()

def test_fastapi_predict_endpoint(client):
    payload = {
        "items": [
            {
                "store_id": "STORE_01",
                "item_id": "ITEM_001",
                "dept_id": "FOODS_1",
                "sell_price": 6.50,
                "is_promo": 0,
                "is_event": 0,
                "is_weekend": 0,
                "day_of_week": 2,
                "day_of_month": 15,
                "month": 6,
                "year": 2024,
                "lag_1": 45.0,
                "lag_7": 42.0,
                "lag_14": 40.0,
                "lag_28": 38.0,
                "rolling_mean_7": 43.5,
                "rolling_std_7": 3.2,
                "rolling_mean_14": 42.0,
                "rolling_std_14": 3.8,
                "rolling_mean_28": 41.0,
                "rolling_std_28": 4.1,
                "price_ratio_28": 1.0,
                "price_diff_7": 0.0,
                "dow_sin": 0.78,
                "dow_cos": 0.62,
                "month_sin": 0.5,
                "month_cos": 0.86
            }
        ]
    }
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 1
    assert data["predictions"][0]["predicted_sales"] >= 0
    assert "model_version" in data
    assert data["latency_ms"] >= 0
    assert data["served_by"] == "champion"

    # Test /ready endpoint
    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"

    # Test fallback degradation on model exception
    from unittest.mock import patch
    with patch("src.serving.app.active_model.predict", side_effect=RuntimeError("CUDA out of memory / Booster error")):
        fail_resp = client.post("/predict", json=payload)
        assert fail_resp.status_code == 200
        fail_data = fail_resp.json()
        assert fail_data["served_by"] == "fallback"
        assert fail_data["predictions"][0]["predicted_sales"] == 42.0  # lag_7 value

def test_fastapi_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "prediction_requests_total" in resp.text
    assert "prediction_fallback_total" in resp.text
    assert "prediction_latency_seconds" in resp.text

def test_fastapi_api_agent_endpoint(client):
    # Test tournament battle request
    payload = {"prompt": "Run model battle arena tournament and compare LightGBM vs ETS vs Naive"}
    resp = client.post("/api/agent", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "RUN_MODEL_BATTLE"
    assert "LightGBM" in data["message"]
    assert "reactSteps" in data
    assert "contextWindow" in data
    assert len(data["suggestedActions"]) > 0

    # Test drift simulation request
    drift_payload = {"prompt": "Simulate a price shock drift in Dairy and evaluate PSI"}
    resp = client.post("/api/agent", json=drift_payload)
    assert resp.status_code == 200
    drift_data = resp.json()
    assert drift_data["action"] == "EXECUTE_DRIFT_SIMULATION"
    assert drift_data["status"] == "ALERT_ACTIVE"
    assert any(k in drift_data["message"] for k in ["0.396", "PSI", "psi", "drift"])
    assert len(drift_data["suggestedActions"]) > 0

    # Test file inspection request
    inspect_payload = {"prompt": "inspect src/models/registry.py"}
    resp = client.post("/api/agent", json=inspect_payload)
    assert resp.status_code == 200
    inspect_data = resp.json()
    assert inspect_data["action"] == "INSPECT_CODE_FILE"
    assert len(inspect_data.get("codeCards", [])) > 0

def test_fastapi_api_battle_endpoint(client):
    payload = {
        "activeDatasetId": "ds_beverages_promo",
        "selectedModels": ["lightgbm", "ets", "s_naive", "moving_avg", "naive"]
    }
    resp = client.post("/api/battle", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["activeDatasetId"] == "ds_beverages_promo"
    assert len(data["results"]) == 5
    assert data["champion"]["shortName"] in ["LightGBM", "L1 Loss"]
    assert "datasetSummary" in data
    assert "tournamentLog" in data

def test_fastapi_api_analyse_endpoint(client):
    # Phase 1: profile
    profile_payload = {
        "phase": "profile",
        "fileName": "test_sales.csv",
        "points": [{"actual": 45.0}, {"actual": 52.0}, {"actual": 60.0}, {"actual": 38.0}]
    }
    resp = client.post("/api/analyse", json=profile_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "profiling" in data
    assert data["profiling"]["totalRows"] == 4
    assert len(data["tradeoffProfiles"]) == 3

    # Phase 2: execute_workflow
    exec_payload = {
        "phase": "execute_workflow",
        "fileName": "test_sales.csv",
        "points": [{"actual": 45.0}, {"actual": 52.0}],
        "selectedTradeoff": {"profile": "balanced", "consentGiven": True}
    }
    resp = client.post("/api/analyse", json=exec_payload)
    assert resp.status_code == 200
    exec_data = resp.json()
    assert exec_data["status"] == "SUCCESS"
    assert "champion" in exec_data

def test_fastapi_api_rag_endpoint(client):
    resp = client.get("/api/rag?query=rollback")
    assert resp.status_code == 200
    data = resp.json()
    assert "sources" in data
    assert len(data["sources"]) > 0
    assert "contextText" in data
