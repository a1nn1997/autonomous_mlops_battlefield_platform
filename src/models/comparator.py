"""
Classical Time-Series Comparator: Holt-Winters Exponential Smoothing (ETS).
Adheres to SOLID Principles:
- Single Responsibility: Implements exponential smoothing state-space model.
- Liskov Substitution: Implements IForecaster and ITrainable contracts.
"""

from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from src.models.base import IForecaster, ITrainable, ForecasterFactory

class ETSComparator(IForecaster, ITrainable):
    """
    Classical Time-Series Comparator: Holt-Winters Exponential Smoothing (ETS).
    Fits seasonal ETS models per item/store or segment to compare against LightGBM.
    """

    def __init__(
        self,
        seasonal_periods: int = 7,
        trend: str = "add",
        seasonal: str = "add",
        group_cols: Optional[List[str]] = None,
        target_col: str = "sales"
    ):
        self.seasonal_periods = seasonal_periods
        self.trend = trend
        self.seasonal = seasonal
        self.group_cols = group_cols or ["store_id", "item_id"]
        self.target_col = target_col
        self.models: Dict[str, Any] = {}

    def fit(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None,
        **kwargs: Any
    ) -> "ETSComparator":
        train_df = train_df.sort_values(by=self.group_cols + ["date"])
        for (store_id, item_id), group in train_df.groupby(self.group_cols):
            key = f"{store_id}_{item_id}"
            y = group[self.target_col].values.astype(float)

            # Need at least 2*seasonal_periods data points for Holt-Winters
            if len(y) >= 2 * self.seasonal_periods:
                try:
                    # Replace zeros with small positive value to allow stable fitting
                    y_clean = np.where(y <= 0, 0.1, y)
                    model = ExponentialSmoothing(
                        y_clean,
                        trend=self.trend,
                        seasonal=self.seasonal,
                        seasonal_periods=self.seasonal_periods,
                        initialization_method="estimated"
                    ).fit(optimized=True)
                    self.models[key] = {
                        "last_fitted_value": float(model.fittedvalues[-1]),
                        "forecast_func": model.forecast,
                        "mean_val": float(np.mean(y))
                    }
                except Exception:
                    # Fallback to simple mean if optimization fails
                    self.models[key] = {"mean_val": float(np.mean(y))}
            else:
                self.models[key] = {"mean_val": float(np.mean(y)) if len(y) > 0 else 10.0}

        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        preds = []
        for _, row in df.iterrows():
            key = f"{row['store_id']}_{row['item_id']}"
            if key in self.models:
                m_info = self.models[key]
                if "forecast_func" in m_info:
                    preds.append(max(0.0, m_info["last_fitted_value"]))
                else:
                    preds.append(max(0.0, m_info["mean_val"]))
            else:
                preds.append(10.0)
        return np.array(preds)

# Register comparator in factory
ForecasterFactory.register_algorithm("ets", ETSComparator)
ForecasterFactory.register_algorithm("holt_winters", ETSComparator)
