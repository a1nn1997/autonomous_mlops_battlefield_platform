"""
Forecast Evaluation Metrics implementing Strategy Pattern.
Follows SOLID Principles:
- Single Responsibility: Discrete strategy classes for each statistical error metric.
- Open/Closed: New metrics (e.g., SMAPE, Pinball Loss) plug in without modifying existing evaluators.
- Liskov Substitution: All strategies conform to IMetricStrategy.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

class IMetricStrategy(ABC):
    """Strategy interface for computing a single forecast evaluation metric."""
    @property
    @abstractmethod
    def name(self) -> str:
        """Metric identifier."""
        pass

    @abstractmethod
    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Computes metric value from ground truth and predicted vectors."""
        pass

class WAPEStrategy(IMetricStrategy):
    """
    Weighted Absolute Percentage Error (WAPE):
    WAPE = sum(|y_true - y_pred|) / sum(y_true)
    """
    @property
    def name(self) -> str:
        return "wape"

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        denom = np.sum(np.abs(y_true))
        if denom == 0:
            return 0.0 if np.sum(np.abs(y_pred)) == 0 else 1.0
        return float(np.sum(np.abs(y_true - y_pred)) / denom)

class BiasStrategy(IMetricStrategy):
    """
    Normalized Forecast Bias:
    Bias = sum(y_pred - y_true) / sum(y_true)
    """
    @property
    def name(self) -> str:
        return "bias"

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        denom = np.sum(np.abs(y_true))
        if denom == 0:
            return 0.0
        return float(np.sum(y_pred - y_true) / denom)

class MAEStrategy(IMetricStrategy):
    """Mean Absolute Error."""
    @property
    def name(self) -> str:
        return "mae"

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        return float(np.mean(np.abs(y_true - y_pred)))

class RMSEStrategy(IMetricStrategy):
    """Root Mean Squared Error."""
    @property
    def name(self) -> str:
        return "rmse"

    def calculate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

class ForecastEvaluationSuite:
    """
    Context class executing a suite of metric strategies across predictions.
    """
    def __init__(self, strategies: Optional[List[IMetricStrategy]] = None):
        self.strategies = strategies or [
            WAPEStrategy(),
            BiasStrategy(),
            MAEStrategy(),
            RMSEStrategy()
        ]

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        results: Dict[str, float] = {}
        for s in self.strategies:
            val = s.calculate(y_true, y_pred)
            if s.name in ("wape", "bias"):
                results[s.name] = round(val, 4)
            else:
                results[s.name] = round(val, 2)
        results["total_actual"] = float(np.sum(y_true))
        results["total_pred"] = float(np.sum(y_pred))
        return results

# Default singleton suite
_DEFAULT_SUITE = ForecastEvaluationSuite()

# Backward-compatible functional APIs
def calculate_wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return WAPEStrategy().calculate(y_true, y_pred)

def calculate_bias(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return BiasStrategy().calculate(y_true, y_pred)

def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return MAEStrategy().calculate(y_true, y_pred)

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return RMSEStrategy().calculate(y_true, y_pred)

def evaluate_forecast(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculates all key summary metrics for a forecast vector."""
    return _DEFAULT_SUITE.evaluate(y_true, y_pred)

def evaluate_by_segment(
    df: pd.DataFrame,
    y_true_col: str = "sales",
    y_pred_col: str = "y_pred",
    segment_cols: List[str] = ["dept_id", "store_id"]
) -> pd.DataFrame:
    """
    Computes WAPE, Bias, MAE, and RMSE grouped by dimensional segments.
    """
    results = []
    for seg_col in segment_cols:
        if seg_col not in df.columns:
            continue
        grouped = df.groupby(seg_col)
        for name, group in grouped:
            y_t = group[y_true_col].values
            y_p = group[y_pred_col].values
            metrics = evaluate_forecast(y_t, y_p)
            results.append({
                "segment_dimension": seg_col,
                "segment_value": str(name),
                "count": len(group),
                "wape": metrics["wape"],
                "bias": metrics["bias"],
                "mae": metrics["mae"],
                "rmse": metrics["rmse"]
            })

    # Add overall row
    overall = evaluate_forecast(df[y_true_col].values, df[y_pred_col].values)
    results.append({
        "segment_dimension": "OVERALL",
        "segment_value": "ALL",
        "count": len(df),
        "wape": overall["wape"],
        "bias": overall["bias"],
        "mae": overall["mae"],
        "rmse": overall["rmse"]
    })

    return pd.DataFrame(results)
