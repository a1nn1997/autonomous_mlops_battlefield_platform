import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.metrics.evaluator import calculate_wape
from src.config import settings

class RollingWAPEDecayMonitor:
    """
    Monitors rolling WAPE degradation over time windows.
    Detects concept drift and model accuracy decay.
    """

    def __init__(
        self,
        window_days: int = settings.drift.window_days,
        decay_threshold: float = settings.drift.wape_decay_threshold,
        date_col: str = "date"
    ):
        self.window_days = window_days
        self.decay_threshold = decay_threshold
        self.date_col = date_col

    def check_decay(
        self,
        baseline_wape: float,
        production_df: pd.DataFrame,
        y_true_col: str = "sales",
        y_pred_col: str = "y_pred"
    ) -> Dict[str, Any]:
        df = production_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[self.date_col]):
            df[self.date_col] = pd.to_datetime(df[self.date_col])

        df = df.sort_values(by=self.date_col)
        unique_dates = np.sort(df[self.date_col].unique())

        if len(unique_dates) < self.window_days:
            # Not enough data for rolling window; evaluate overall
            curr_wape = calculate_wape(df[y_true_col].values, df[y_pred_col].values)
            relative_decay = (curr_wape - baseline_wape) / max(0.01, baseline_wape)
            return {
                "alert": relative_decay >= self.decay_threshold,
                "baseline_wape": round(baseline_wape, 4),
                "current_wape": round(curr_wape, 4),
                "relative_decay": round(relative_decay, 4),
                "window_count": 1,
                "decay_history": [{"date": str(unique_dates[-1]), "wape": round(curr_wape, 4)}]
            }

        # Calculate rolling window WAPE
        decay_history = []
        for i in range(len(unique_dates) - self.window_days + 1):
            window_dates = unique_dates[i : i + self.window_days]
            window_df = df[df[self.date_col].isin(window_dates)]
            w_wape = calculate_wape(window_df[y_true_col].values, window_df[y_pred_col].values)
            decay_history.append({
                "end_date": str(window_dates[-1])[:10],
                "wape": round(w_wape, 4)
            })

        latest_wape = decay_history[-1]["wape"]
        relative_decay = (latest_wape - baseline_wape) / max(0.01, baseline_wape)
        alert = relative_decay >= self.decay_threshold

        return {
            "alert": alert,
            "baseline_wape": round(baseline_wape, 4),
            "current_wape": round(latest_wape, 4),
            "relative_decay": round(relative_decay, 4),
            "threshold": self.decay_threshold,
            "decay_history": decay_history
        }
