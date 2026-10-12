import pytest
import pandas as pd
import numpy as np
from src.data.dataset import generate_retail_data
from src.data.features import FeaturePipeline
from src.data.split import TimeBasedSplitter

def test_generate_retail_data():
    df = generate_retail_data(n_items=4, n_stores=2, start_date="2023-01-01", end_date="2023-03-31")
    assert not df.empty
    assert "sales" in df.columns
    assert "sell_price" in df.columns
    assert "is_promo" in df.columns
    assert df["store_id"].nunique() == 2
    assert df["item_id"].nunique() == 4
    # All sales values should be non-negative integers
    assert (df["sales"] >= 0).all()

def test_feature_pipeline():
    raw_df = generate_retail_data(n_items=2, n_stores=2, start_date="2023-01-01", end_date="2023-04-30")
    pipeline = FeaturePipeline()
    feat_df = pipeline.fit_transform(raw_df, drop_na=True)
    
    assert "lag_1" in feat_df.columns
    assert "lag_7" in feat_df.columns
    assert "rolling_mean_7" in feat_df.columns
    assert "price_ratio_28" in feat_df.columns
    assert "dow_sin" in feat_df.columns
    assert not feat_df.isnull().any().any()

def test_time_based_splitter_no_leakage():
    raw_df = generate_retail_data(n_items=2, n_stores=2, start_date="2023-01-01", end_date="2023-06-30")
    pipeline = FeaturePipeline()
    feat_df = pipeline.fit_transform(raw_df)

    splitter = TimeBasedSplitter(train_end="2023-04-30", val_end="2023-05-31", test_end="2023-06-30")
    train, val, test = splitter.split(feat_df)

    assert train["date"].max() <= pd.to_datetime("2023-04-30")
    assert val["date"].min() > pd.to_datetime("2023-04-30")
    assert val["date"].max() <= pd.to_datetime("2023-05-31")
    assert test["date"].min() > pd.to_datetime("2023-05-31")
    assert test["date"].max() <= pd.to_datetime("2023-06-30")
