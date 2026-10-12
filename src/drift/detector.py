"""
Distribution drift monitoring implementing Strategy Pattern and IDriftDetector interface.
Follows SOLID Principles:
- Single Responsibility: Statistical distribution stability evaluation via PSI and KS-tests.
- Open/Closed: Extensible detector interface for multivariate drift telemetry.
- Liskov Substitution: All drift detectors adhere to IDriftDetector contract.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from src.config import settings

def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_bins: int = 10,
    epsilon: float = 1e-4
) -> float:
    """
    Computes Population Stability Index (PSI) between baseline (expected)
    and production monitoring (actual) distributions.
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(expected, percentiles)
    bin_edges = np.unique(bin_edges)

    if len(bin_edges) < 2:
        return 0.0

    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)

    expected_pct = np.where(expected_pct == 0, epsilon, expected_pct)
    actual_pct = np.where(actual_pct == 0, epsilon, actual_pct)

    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(max(0.0, psi_val))

def calculate_ks(expected: np.ndarray, actual: np.ndarray) -> Tuple[float, float]:
    """
    Two-sample Kolmogorov-Smirnov test.
    Returns (ks_statistic, p_value).
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    if len(expected) == 0 or len(actual) == 0:
        return 0.0, 1.0
    res = stats.ks_2samp(expected, actual)
    return float(res.statistic), float(res.pvalue)

class IDriftDetector(ABC):
    """
    Abstract contract for statistical distribution drift detection.
    """
    @abstractmethod
    def analyze_drift(
        self,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        baseline_preds: Optional[np.ndarray] = None,
        current_preds: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Analyzes distribution shift between reference and live dataframes."""
        pass

class DriftDetector(IDriftDetector):
    """
    Monitors distribution drift across features and model predictions.
    Computes PSI and KS-tests against a baseline reference dataset.
    """

    def __init__(
        self,
        features_to_monitor: Optional[List[str]] = None,
        psi_warning: float = settings.drift.psi_warning_threshold,
        psi_critical: float = settings.drift.psi_critical_threshold,
        ks_alpha: float = settings.drift.ks_significance_level
    ):
        self.features_to_monitor = features_to_monitor or [
            "sell_price", "lag_1", "lag_7", "rolling_mean_7", "rolling_mean_28"
        ]
        self.psi_warning = psi_warning
        self.psi_critical = psi_critical
        self.ks_alpha = ks_alpha

    def analyze_drift(
        self,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        baseline_preds: Optional[np.ndarray] = None,
        current_preds: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Runs full drift analysis over monitored features and prediction output."""
        feature_reports = {}
        drift_detected = False
        max_psi = 0.0

        for col in self.features_to_monitor:
            if col in baseline_df.columns and col in current_df.columns:
                base_vals = baseline_df[col].dropna().values
                curr_vals = current_df[col].dropna().values

                psi = calculate_psi(base_vals, curr_vals)
                ks_stat, p_val = calculate_ks(base_vals, curr_vals)

                status = "STABLE"
                if psi >= self.psi_critical or (p_val < self.ks_alpha and psi >= self.psi_warning):
                    status = "CRITICAL_DRIFT"
                    drift_detected = True
                elif psi >= self.psi_warning:
                    status = "WARNING"

                max_psi = max(max_psi, psi)
                feature_reports[col] = {
                    "psi": round(psi, 4),
                    "ks_statistic": round(ks_stat, 4),
                    "ks_p_value": round(p_val, 5),
                    "status": status,
                    "baseline_mean": round(float(np.mean(base_vals)), 2),
                    "current_mean": round(float(np.mean(curr_vals)), 2)
                }

        # Prediction drift
        pred_report = None
        if baseline_preds is not None and current_preds is not None:
            pred_psi = calculate_psi(baseline_preds, current_preds)
            ks_stat, p_val = calculate_ks(baseline_preds, current_preds)
            pred_status = "CRITICAL_DRIFT" if pred_psi >= self.psi_critical else ("WARNING" if pred_psi >= self.psi_warning else "STABLE")
            if pred_status == "CRITICAL_DRIFT":
                drift_detected = True
            pred_report = {
                "psi": round(pred_psi, 4),
                "ks_statistic": round(ks_stat, 4),
                "ks_p_value": round(p_val, 5),
                "status": pred_status,
                "baseline_mean": round(float(np.mean(baseline_preds)), 2),
                "current_mean": round(float(np.mean(current_preds)), 2)
            }

        return {
            "drift_detected": drift_detected,
            "max_psi": round(max_psi, 4),
            "features": feature_reports,
            "predictions": pred_report,
            "sample_counts": {
                "baseline": len(baseline_df),
                "current": len(current_df)
            }
        }
