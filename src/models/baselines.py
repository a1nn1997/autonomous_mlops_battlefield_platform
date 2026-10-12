"""
Statistical baseline forecasters implementing IForecaster contract.
Follows SOLID Principles:
- Single Responsibility: Implements deterministic temporal lag projections.
- Liskov Substitution: Satisfies IForecaster predict() contract.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
from src.models.base import IForecaster, ForecasterFactory

class NaiveBaseline(IForecaster):
    """
    Persistence baseline: predicts t using t-1.
    If lag_1 column exists, uses it; otherwise computes shift(1) by group.
    """
    def __init__(
        self,
        group_cols: Optional[List[str]] = None,
        target_col: str = "sales"
    ):
        self.group_cols = group_cols or ["store_id", "item_id"]
        self.target_col = target_col

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if "lag_1" in df.columns:
            return df["lag_1"].fillna(0.0).values
        return df.groupby(self.group_cols)[self.target_col].shift(1).fillna(0.0).values

class SeasonalNaiveBaseline(IForecaster):
    """
    Seasonal persistence baseline: predicts t using t-7 (same day of week).
    If lag_7 column exists, uses it; otherwise computes shift(7) by group.
    """
    def __init__(
        self,
        group_cols: Optional[List[str]] = None,
        target_col: str = "sales",
        season_length: int = 7
    ):
        self.group_cols = group_cols or ["store_id", "item_id"]
        self.target_col = target_col
        self.season_length = season_length

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        lag_col = f"lag_{self.season_length}"
        if lag_col in df.columns:
            return df[lag_col].fillna(0.0).values
        return df.groupby(self.group_cols)[self.target_col].shift(self.season_length).fillna(0.0).values

class MovingAverageBaseline(IForecaster):
    """
    Moving Average baseline: predicts t using rolling mean of past window_size days.
    """
    def __init__(
        self,
        group_cols: Optional[List[str]] = None,
        target_col: str = "sales",
        window_size: int = 7
    ):
        self.group_cols = group_cols or ["store_id", "item_id"]
        self.target_col = target_col
        self.window_size = window_size

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        rolling_col = f"rolling_mean_{self.window_size}"
        if rolling_col in df.columns:
            return df[rolling_col].fillna(0.0).values
        return (
            df.groupby(self.group_cols)[self.target_col]
            .transform(lambda s: s.shift(1).rolling(self.window_size, min_periods=1).mean())
            .fillna(0.0)
            .values
        )

# Register baselines in ForecasterFactory
ForecasterFactory.register_algorithm("naive", NaiveBaseline)
ForecasterFactory.register_algorithm("seasonal_naive", SeasonalNaiveBaseline)
ForecasterFactory.register_algorithm("moving_average", MovingAverageBaseline)
