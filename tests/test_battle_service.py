import pytest
import numpy as np
import pandas as pd
from src.battle_service import parse_csv_to_dataframe, parse_csv_to_series, run_model_battle

def test_parse_csv_to_dataframe_valid_and_invalid():
    # Empty CSV
    with pytest.raises(ValueError, match="empty or has only a header row"):
        parse_csv_to_dataframe("date,sales\n")

    # CSV with fewer than 60 rows
    short_rows = ["date,sales"] + [f"2024-01-{i+1:02d},50" for i in range(30)]
    short_csv = "\n".join(short_rows)
    with pytest.raises(ValueError, match="at least 60 rows"):
        parse_csv_to_dataframe(short_csv)

    # Valid CSV with 70 rows
    valid_rows = ["date,sales,store_id,item_id"] + [f"2024-01-{i+1:02d},{50+i%5},STORE_01,ITEM_001" for i in range(70)]
    valid_csv = "\n".join(valid_rows)
    df = parse_csv_to_dataframe(valid_csv)
    assert len(df) == 70
    assert "date" in df.columns
    assert "sales" in df.columns
    assert "store_id" in df.columns
    assert "item_id" in df.columns

def test_parse_csv_to_series_no_simulated_forecasts():
    # If < 60 rows, raises ValueError without any simulated path
    short_csv = "date,sales\n2024-01-01,10\n2024-01-02,20\n"
    with pytest.raises(ValueError, match="at least 60 rows"):
        parse_csv_to_series(short_csv)

    # Valid CSV produces only date and actual, NO simulated lightgbm or ets keys
    valid_rows = ["date,sales"] + [f"2024-01-{i+1:02d},{40+(i%7)*3}" for i in range(70)]
    valid_csv = "\n".join(valid_rows)
    points = parse_csv_to_series(valid_csv)
    assert len(points) == 70
    assert "date" in points[0]
    assert "actual" in points[0]
    assert "lightgbm" not in points[0]
    assert "ets" not in points[0]
    assert "naive" not in points[0]

@pytest.mark.asyncio
async def test_run_model_battle_custom_csv_real_training():
    dates = pd.date_range("2024-01-01", periods=75, freq="D")
    sales = [45.0 + (i % 7) * 4.0 for i in range(75)]
    csv_rows = ["date,sales,store_id,item_id"]
    for d, s in zip(dates, sales):
        csv_rows.append(f"{d.strftime('%Y-%m-%d')},{s},STORE_01,ITEM_001")
    custom_csv = "\n".join(csv_rows)

    payload = {
        "activeDatasetId": "custom_real",
        "datasets": [{"id": "custom_real", "name": "Real Training Data", "csvContent": custom_csv}],
        "selectedModels": ["lightgbm", "ets", "s_naive", "naive", "moving_avg"]
    }
    res = await run_model_battle(payload)
    assert res["measured"] is True
    assert len(res["results"]) == 5
    champ = res["champion"]
    assert champ["measured"] is True
    assert champ["latencyP50"] > 0
    assert champ["throughputRps"] > 0
    assert champ["memoryMb"] > 0
    assert 0.0 <= champ["wape"] <= 1.0

@pytest.mark.asyncio
async def test_run_model_battle_preloaded_dataset_real_training():
    # Preloaded datasets now execute the same real train-and-measure pipeline
    payload = {
        "activeDatasetId": "m5_sample",
        "datasets": [],
        "selectedModels": ["lightgbm", "ets", "naive"]
    }
    res = await run_model_battle(payload)
    assert res["measured"] is True
    assert len(res["results"]) == 3
    # Check that latency is measured, not hardcoded profiles
    for m in res["results"]:
        assert m["measured"] is True
        assert m["latencyP50"] > 0
        assert m["throughputRps"] > 0
        assert m["memoryMb"] > 0
