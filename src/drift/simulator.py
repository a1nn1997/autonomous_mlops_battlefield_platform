import numpy as np
import pandas as pd
from typing import Optional, Literal
from src.data.features import FeaturePipeline

class DriftSimulator:
    """
    Injects synthetic distribution shifts to simulate production drift.
    Supports:
      - 'price_shock': 50% price inflation causing demand contractions
      - 'promo_surge': Massive unannounced promotion blitz causing demand surges
      - 'demand_drop': Exogenous economic contraction reducing demand by 45%
      - 'weekend_shift': Shift in shopping habit away from weekends
    """

    @staticmethod
    def inject_drift(
        df: pd.DataFrame,
        shift_type: Literal["price_shock", "promo_surge", "demand_drop", "weekend_shift"] = "price_shock",
        slice_fraction: float = 0.5,
        seed: int = 99
    ) -> pd.DataFrame:
        np.random.seed(seed)
        df_shifted = df.copy()

        # Slice the latter portion of time series to inject drift
        split_idx = int(len(df_shifted) * (1.0 - slice_fraction))
        drift_mask = df_shifted.index >= split_idx

        if shift_type == "price_shock":
            # Increase sell price by 60%, dampening sales
            df_shifted.loc[drift_mask, "sell_price"] = df_shifted.loc[drift_mask, "sell_price"] * 1.6
            df_shifted.loc[drift_mask, "sales"] = (df_shifted.loc[drift_mask, "sales"] * 0.55).astype(int)

        elif shift_type == "promo_surge":
            # Force high promo rate and demand explosion
            df_shifted.loc[drift_mask, "is_promo"] = 1
            df_shifted.loc[drift_mask, "sell_price"] = df_shifted.loc[drift_mask, "sell_price"] * 0.75
            df_shifted.loc[drift_mask, "sales"] = (df_shifted.loc[drift_mask, "sales"] * 2.2).astype(int)

        elif shift_type == "demand_drop":
            # Structural decrease in demand across stores
            df_shifted.loc[drift_mask, "sales"] = (df_shifted.loc[drift_mask, "sales"] * 0.40).astype(int)

        elif shift_type == "weekend_shift":
            # Flip weekend boost to mid-week
            midweek_mask = drift_mask & (df_shifted["day_of_week"].isin([1, 2]))
            df_shifted.loc[midweek_mask, "sales"] = (df_shifted.loc[midweek_mask, "sales"] * 2.0).astype(int)

        # Recompute lagged and rolling features on the shifted data
        pipeline = FeaturePipeline()
        refreshed_df = pipeline.fit_transform(df_shifted, drop_na=True)
        return refreshed_df
