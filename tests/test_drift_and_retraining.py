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

def test_promotion_gate_decisions():
    from src.metrics.gates import evaluate_promotion_gate
    np.random.seed(42)
    y_true = np.array([50.0 + i for i in range(30)])

    # 1. Promote case: Challenger significantly better, low bias
    # Both have low bias, challenger has much smaller error
    champ_preds = y_true + np.where(np.arange(30) % 2 == 0, 8.0, -8.0)  # zero bias, error=8
    chal_preds = y_true + np.where(np.arange(30) % 2 == 0, 1.0, -1.0)   # zero bias, error=1
    res_promote = evaluate_promotion_gate(y_true, champ_preds, chal_preds, wilcoxon_alpha=0.05, max_absolute_bias=0.05)
    assert res_promote["decision"] == "PROMOTED"
    assert res_promote["is_promoted"] is True
    assert res_promote["wilcoxon_p_value"] < 0.05

    # 2. Reject worse: Challenger has worse WAPE
    chal_worse = y_true + np.where(np.arange(30) % 2 == 0, 12.0, -12.0)
    res_worse = evaluate_promotion_gate(y_true, champ_preds, chal_worse, wilcoxon_alpha=0.05, max_absolute_bias=0.05)
    assert res_worse["decision"] == "REJECTED_WORSE_WAPE"
    assert res_worse["is_promoted"] is False

    # 3. Reject not significant: Challenger only has tiny, mixed jitter around champion
    # e.g. very slight improvements on half the points, identical on rest
    jitter = np.zeros(30)
    jitter[0] = -0.5
    jitter[1] = 0.5
    chal_similar = champ_preds + jitter
    res_not_sig = evaluate_promotion_gate(y_true, champ_preds, chal_similar, wilcoxon_alpha=0.01, max_absolute_bias=0.05)
    assert res_not_sig["is_promoted"] is False
    assert res_not_sig["decision"] in ["REJECTED_NOT_SIGNIFICANT", "REJECTED_WORSE_WAPE"]

    # 4. Reject bias violation: Challenger achieves lower WAPE but violates bias bound
    # e.g., large directional under-prediction
    chal_biased = y_true * 0.92  # -8% bias, exceeding 5% bound
    res_bias = evaluate_promotion_gate(y_true, champ_preds, chal_biased, wilcoxon_alpha=0.05, max_absolute_bias=0.05)
    assert res_bias["decision"] == "REJECTED_BIAS_VIOLATION"
    assert res_bias["is_promoted"] is False
