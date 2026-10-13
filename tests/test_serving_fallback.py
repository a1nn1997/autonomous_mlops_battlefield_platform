import pytest
import asyncio
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient

from src.serving.app import app, load_active_model
import src.serving.app as serving_module
import src.serving.middleware as mw
from src.data.dataset import generate_retail_data
from src.data.features import FeaturePipeline
from src.models.lightgbm_model import LightGBMForecaster

@pytest.fixture(scope="module")
def client():
    load_active_model()
    if serving_module.active_model is None:
        raw_df = generate_retail_data(n_items=2, n_stores=1, start_date="2024-01-01", end_date="2024-03-31")
        pipeline = FeaturePipeline()
        feat_df = pipeline.fit_transform(raw_df)
        m = LightGBMForecaster(params={"n_estimators": 10, "verbose": -1})
        m.fit(feat_df)
        serving_module.registry.register("v1", m, {"wape": 0.13}, description="Serving Fallback Fixture", promote=True)
        load_active_model()
    return TestClient(app)

def get_valid_payload():
    return {
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

def test_serving_normal_champion(client):
    payload = get_valid_payload()
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["served_by"] == "champion"
    assert len(data["predictions"]) == 1

def test_serving_exception_triggers_fallback(client):
    initial_fallbacks = mw.fallback_counter
    payload = get_valid_payload()

    # Simulate catastrophic inference failure (e.g., CUDA / memory fault)
    with patch.object(serving_module.active_model, "predict", side_effect=RuntimeError("Booster runtime panic")):
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["served_by"] == "fallback"
        assert data["model_version"] == "fallback_seasonal_naive"
        assert data["predictions"][0]["predicted_sales"] == 42.0  # Uses lag_7
        assert mw.fallback_counter > initial_fallbacks

def test_serving_active_model_none_fallback(client):
    payload = get_valid_payload()

    # Simulate active_model being None
    with patch.object(serving_module, "active_model", None):
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["served_by"] == "fallback"
        assert data["model_version"] == "fallback_seasonal_naive"
        assert data["predictions"][0]["predicted_sales"] == 42.0

@pytest.mark.asyncio
async def test_serving_timeout_triggers_fallback():
    # Test TimeoutMiddleware directly to verify SLA breach handling
    async def slow_endpoint(request):
        await asyncio.sleep(0.1)
        return None

    middleware = mw.TimeoutMiddleware(slow_endpoint, timeout_seconds=0.01)

    # Mock a request to /predict
    mock_request = MagicMock()
    mock_request.url.path = "/predict"
    
    async def mock_json():
        return {"items": [{"store_id": "STORE_01", "item_id": "ITEM_001", "lag_7": 42.0}]}

    mock_request.json = mock_json

    resp = await middleware.dispatch(mock_request, slow_endpoint)
    assert resp.status_code == 200
    import json
    body = json.loads(resp.body.decode("utf-8"))
    assert body["served_by"] == "fallback"
    assert body["model_version"] == "fallback_seasonal_naive"
    assert body["predictions"][0]["predicted_sales"] == 42.0
    assert body["predictions"][0]["predicted_sales"] == 42.0
