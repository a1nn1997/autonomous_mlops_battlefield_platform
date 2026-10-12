import pytest
import numpy as np
import pandas as pd
from src.metrics.evaluator import calculate_wape, calculate_bias, evaluate_forecast
from src.models.baselines import NaiveBaseline, SeasonalNaiveBaseline
from src.models.lightgbm_model import LightGBMForecaster
from src.models.comparator import ETSComparator
from src.data.dataset import generate_retail_data
from src.data.features import FeaturePipeline
from src.data.split import TimeBasedSplitter

def test_metrics_evaluator():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0])
    # abs diff: 2 + 2 + 3 = 7, sum y_true = 60 => WAPE = 7/60 ~ 0.1167
    wape = calculate_wape(y_true, y_pred)
    assert abs(wape - (7 / 60)) < 1e-4

    # bias: (12-10) + (18-20) + (33-30) = 2 - 2 + 3 = 3 / 60 = 0.05
    bias = calculate_bias(y_true, y_pred)
    assert abs(bias - 0.05) < 1e-4

def test_baselines_and_lightgbm():
    raw_df = generate_retail_data(n_items=2, n_stores=2, start_date="2023-01-01", end_date="2023-06-30")
    pipeline = FeaturePipeline()
    feat_df = pipeline.fit_transform(raw_df)
    splitter = TimeBasedSplitter(train_end="2023-04-30", val_end="2023-05-31", test_end="2023-06-30")
    train, val, test = splitter.split(feat_df)
    y_test = test["sales"].values

    # Naive
    naive = NaiveBaseline()
    n_preds = naive.predict(test)
    assert len(n_preds) == len(test)

    # Seasonal Naive
    s_naive = SeasonalNaiveBaseline()
    sn_preds = s_naive.predict(test)
    assert len(sn_preds) == len(test)

    # LightGBM
    lgbm = LightGBMForecaster(params={"n_estimators": 50, "learning_rate": 0.05, "verbose": -1})
    lgbm.fit(train, val_df=val)
    preds = lgbm.predict(test)
    assert len(preds) == len(test)
    assert (preds >= 0).all()

    # Moving Average
    from src.models.baselines import MovingAverageBaseline
    from src.models.base import ForecasterFactory
    ma = MovingAverageBaseline(window_size=7)
    ma_preds = ma.predict(test)
    assert len(ma_preds) == len(test)

    # Factory instantiation
    factory_naive = ForecasterFactory.create("naive")
    assert isinstance(factory_naive, NaiveBaseline)
    factory_snaive = ForecasterFactory.create("seasonal_naive", season_length=14)
    assert isinstance(factory_snaive, SeasonalNaiveBaseline)
    assert factory_snaive.season_length == 14
    factory_ma = ForecasterFactory.create("moving_average", window_size=14)
    assert isinstance(factory_ma, MovingAverageBaseline)
    assert factory_ma.window_size == 14

@pytest.mark.asyncio
async def test_battle_service_direct():
    from src.battle_service import parse_csv_to_series, run_model_battle
    short_csv = "date,sales\n2023-01-01,100\n2023-01-02,120\n"
    points = parse_csv_to_series(short_csv)
    assert len(points) == 2
    assert points[0]["actual"] == 100.0

    # Test that < 60 rows raises ValueError with expected message
    short_payload = {
        "activeDatasetId": "custom_short",
        "datasets": [{"id": "custom_short", "name": "Short Dataset", "csvContent": short_csv}],
        "selectedModels": ["lightgbm", "ets", "naive"]
    }
    with pytest.raises(ValueError, match="at least 60 rows"):
        await run_model_battle(short_payload)

    # Test run_model_battle with real models on >= 60 rows
    dates = pd.date_range("2023-01-01", periods=70, freq="D")
    sales = [50.0 + (i % 7) * 5.0 for i in range(70)]
    csv_rows = ["date,sales,store_id,item_id"]
    for d, s in zip(dates, sales):
        csv_rows.append(f"{d.strftime('%Y-%m-%d')},{s},STORE_01,ITEM_001")
    valid_csv = "\n".join(csv_rows)

    payload = {
        "activeDatasetId": "custom_real",
        "datasets": [{"id": "custom_real", "name": "Real Training Data", "csvContent": valid_csv}],
        "selectedModels": ["lightgbm", "ets", "naive", "s_naive", "moving_avg"]
    }
    battle_res = await run_model_battle(payload)
    assert "results" in battle_res
    assert len(battle_res["results"]) == 5
    assert battle_res["measured"] is True
    assert "champion" in battle_res
    assert battle_res["champion"]["measured"] is True
    assert battle_res["champion"]["latencyP50"] > 0
    assert len(battle_res["timeSeries"]) > 0
    # Deterministic metric sanity check
    assert 0.0 <= battle_res["champion"]["wape"] <= 1.0
