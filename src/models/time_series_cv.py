import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from src.metrics.evaluator import calculate_wape, calculate_bias
from src.models.lightgbm_model import LightGBMForecaster

class TimeSeriesCV:
    """
    Expanding-window walk-forward Cross-Validation for temporal series.
    Evaluates out-of-sample WAPE and Bias across multiple forecast horizons.
    """

    def __init__(self, n_splits: int = 4, test_days: int = 14, date_col: str = "date"):
        self.n_splits = n_splits
        self.test_days = test_days
        self.date_col = date_col

    def split(self, df: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[self.date_col]):
            df[self.date_col] = pd.to_datetime(df[self.date_col])

        unique_dates = np.sort(df[self.date_col].unique())
        total_days = len(unique_dates)
        folds = []

        for i in range(self.n_splits, 0, -1):
            test_end_idx = total_days - (i - 1) * self.test_days
            test_start_idx = test_end_idx - self.test_days
            
            if test_start_idx < 30:  # Require at least 30 days of training
                continue

            train_dates = unique_dates[:test_start_idx]
            test_dates = unique_dates[test_start_idx:test_end_idx]

            train_df = df[df[self.date_col].isin(train_dates)].copy()
            test_df = df[df[self.date_col].isin(test_dates)].copy()
            folds.append((train_df, test_df))

        return folds

    def evaluate(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        folds = self.split(df)
        fold_results = []

        for fold_idx, (train_fold, test_fold) in enumerate(folds):
            forecaster = LightGBMForecaster(params=params.copy())
            forecaster.fit(train_fold)
            preds = forecaster.predict(test_fold)
            y_true = test_fold["sales"].values

            wape = calculate_wape(y_true, preds)
            bias = calculate_bias(y_true, preds)

            fold_results.append({
                "fold": fold_idx + 1,
                "train_days": train_fold[self.date_col].nunique(),
                "test_days": test_fold[self.date_col].nunique(),
                "wape": round(wape, 4),
                "bias": round(bias, 4)
            })

        wapes = [f["wape"] for f in fold_results]
        biases = [f["bias"] for f in fold_results]

        return {
            "mean_wape": round(float(np.mean(wapes)), 4) if wapes else 0.0,
            "std_wape": round(float(np.std(wapes)), 4) if wapes else 0.0,
            "mean_bias": round(float(np.mean(biases)), 4) if biases else 0.0,
            "folds": fold_results
        }
