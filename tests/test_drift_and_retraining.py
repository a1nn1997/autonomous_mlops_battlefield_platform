import pytest
import numpy as np
import pandas as pd
from src.drift.detector import calculate_psi, calculate_ks, DriftDetector
from src.drift.simulator import DriftSimulator
from src.drift.decay import RollingWAPEDecayMonitor
from src.data.dataset import generate_retail_data
from src.data.features import FeaturePipeline

def test_psi_and_ks():
    baseline = np.random.normal(10.0, 1.0, 1000)
    # Similar distribution: PSI should be near 0
    similar = np.random.normal(10.0, 1.0, 1000)
    psi_stable = calculate_psi(baseline, similar)
    assert psi_stable < 0.10

    # Drifting distribution: PSI should be large
    drifted = np.random.normal(18.0, 1.5, 1000)
    psi_drift = calculate_psi(baseline, drifted)
    assert psi_drift > 0.25

    ks_stat, ks_p = calculate_ks(baseline, drifted)
    assert ks_p < 0.001

def test_drift_simulator_and_detector():
    raw_df = generate_retail_data(n_items=2, n_stores=2, start_date="2023-01-01", end_date="2023-04-30")
    pipeline = FeaturePipeline()
    base_df = pipeline.fit_transform(raw_df)

    shifted_df = DriftSimulator.inject_drift(raw_df, shift_type="price_shock")
    assert not shifted_df.empty

    detector = DriftDetector()
    report = detector.analyze_drift(base_df, shifted_df)
    assert "max_psi" in report
    assert "features" in report

def test_rolling_wape_decay():
    dates = pd.date_range("2023-01-01", periods=20, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "sales": [100] * 20,
        "y_pred": [80] * 20  # WAPE = 20%
    })
    monitor = RollingWAPEDecayMonitor(window_days=7, decay_threshold=0.15)
    # If baseline is 10%, a current WAPE of 20% is a 100% relative degradation -> alert True
    report = monitor.check_decay(baseline_wape=0.10, production_df=df)
    assert report["alert"] is True
    assert report["current_wape"] == 0.20
