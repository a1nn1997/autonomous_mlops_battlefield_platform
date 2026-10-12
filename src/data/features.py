import numpy as np
import pandas as pd
from typing import List, Tuple
from src.config import settings

class FeaturePipeline:
    """
    Feature pipeline for multi-series retail demand forecasting.
    Includes:
      - Grouped lag features (t-1, t-7, t-14, t-28)
      - Grouped rolling window statistics (7d, 14d, 28d) shifted by 1 to prevent target leakage
      - Price & promotional elasticity indicators
      - Calendar & cyclical seasonality encodings
    """

    def __init__(
        self,
        lags: List[int] = settings.features.lags,
        rolling_windows: List[int] = settings.features.rolling_windows,
        group_cols: List[str] = ["store_id", "item_id"],
        target_col: str = "sales"
    ):
        self.lags = lags
        self.rolling_windows = rolling_windows
        self.group_cols = group_cols
        self.target_col = target_col

    def fit_transform(self, df: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:
        """Transforms raw retail sales dataframe into feature-engineered matrix."""
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"])

        df = df.sort_values(by=self.group_cols + ["date"]).reset_index(drop=True)

        # 1. Calendar & cyclical features
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day_of_month"] = df["date"].dt.day
        df["month"] = df["date"].dt.month
        df["year"] = df["date"].dt.year
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

        # Cyclical transforms (preserve periodic continuity)
        df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
        df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)

        # 2. Lag features (per item-store series)
        for lag in self.lags:
            col_name = f"lag_{lag}"
            df[col_name] = df.groupby(self.group_cols)[self.target_col].shift(lag)

        # 3. Rolling window statistics (shifted by 1 to guarantee zero leakage)
        for w in self.rolling_windows:
            df[f"rolling_mean_{w}"] = df.groupby(self.group_cols)[self.target_col].transform(
                lambda s: s.shift(1).rolling(w).mean()
            )
            df[f"rolling_std_{w}"] = df.groupby(self.group_cols)[self.target_col].transform(
                lambda s: s.shift(1).rolling(w).std()
            ).fillna(0.0)

        # 4. Price dynamics (relative to past rolling price)
        price_mean_28 = df.groupby(self.group_cols)["sell_price"].transform(
            lambda s: s.shift(1).rolling(28).mean()
        )
        df["price_ratio_28"] = (df["sell_price"] / price_mean_28).fillna(1.0)
        df["price_diff_7"] = df.groupby(self.group_cols)["sell_price"].diff(7).fillna(0.0)

        # Ensure promotional flag exists
        if "is_promo" not in df.columns:
            df["is_promo"] = 0
        if "is_event" not in df.columns:
            df["is_event"] = 0

        # Cast categoricals
        for cat in ["store_id", "item_id", "dept_id"]:
            if cat in df.columns:
                df[cat] = df[cat].astype("category")

        if drop_na:
            df = df.dropna().reset_index(drop=True)

        return df

    def transform_single_row(self, history_df: pd.DataFrame, current_row: dict) -> pd.DataFrame:
        """
        Appends current_row to history_df, executes feature engineering,
        and returns the feature vector for current_row.
        """
        row_df = pd.DataFrame([current_row])
        combined = pd.concat([history_df, row_df], ignore_index=True)
        transformed = self.fit_transform(combined, drop_na=False)
        return transformed.iloc[[-1]]
