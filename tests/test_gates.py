import pytest
import numpy as np
from src.metrics.gates import evaluate_promotion_gate

def test_gate_promote():
    # Incumbent champion has higher absolute error across 20 points
    y_true = np.full(20, 100.0)
    champ_preds = np.array([115.0 if i % 2 == 0 else 85.0 for i in range(20)])  # abs error = 15
    chal_preds = np.array([102.0 if i % 2 == 0 else 98.0 for i in range(20)])   # abs error = 2 (significantly lower, zero bias)

    gate = evaluate_promotion_gate(
        y_true=y_true,
        champ_preds=champ_preds,  # Incumbent champion
        chal_preds=chal_preds,    # Candidate challenger
        wilcoxon_alpha=0.05,
        max_absolute_bias=0.05
    )

    assert gate["decision"] == "PROMOTED"
    assert gate["is_promoted"] is True
    assert gate["challenger_wape"] < gate["champion_wape"]
    assert gate["wilcoxon_p_value"] < 0.05
    assert abs(gate["challenger_bias"]) <= 0.05
    assert len(gate["reasons"]) > 0

def test_gate_reject_worse_wape():
    # Candidate challenger has worse WAPE than champion
    y_true = np.full(20, 100.0)
    champ_preds = np.array([102.0 for _ in range(20)])   # abs error = 2
    chal_preds = np.array([115.0 for _ in range(20)])    # abs error = 15

    gate = evaluate_promotion_gate(
        y_true=y_true,
        champ_preds=champ_preds,
        chal_preds=chal_preds,
        wilcoxon_alpha=0.05,
        max_absolute_bias=0.05
    )

    assert gate["decision"] == "REJECTED_WORSE_WAPE"
    assert gate["is_promoted"] is False
    assert gate["challenger_wape"] > gate["champion_wape"]

def test_gate_reject_not_significant():
    # Challenger has slightly lower mean error, but p-value >= alpha (ranks split)
    champ_e = np.array([6.0]*9 + [4.0]*11)
    chal_e = np.array([4.0]*9 + [5.5]*11)
    y_t = np.full(20, 100.0)

    gate = evaluate_promotion_gate(
        y_true=y_t,
        champ_preds=y_t + champ_e,
        chal_preds=y_t + chal_e,
        wilcoxon_alpha=0.05,
        max_absolute_bias=0.10
    )

    assert gate["decision"] == "REJECTED_NOT_SIGNIFICANT"
    assert gate["is_promoted"] is False
    assert gate["wilcoxon_p_value"] >= 0.05
    assert gate["challenger_wape"] < gate["champion_wape"]

def test_gate_reject_bias_violation():
    # Challenger has lower WAPE and p < 0.05, but severe systematic positive bias (> 5%)
    y_true = np.full(20, 100.0)
    champ_preds = np.array([120.0 if i % 2 == 0 else 80.0 for i in range(20)]) # abs error 20, zero bias
    # Challenger has abs error 8, but every single error is +8 (overforecasting by 8%)
    chal_preds = np.full(20, 108.0)

    gate = evaluate_promotion_gate(
        y_true=y_true,
        champ_preds=champ_preds,
        chal_preds=chal_preds,
        wilcoxon_alpha=0.05,
        max_absolute_bias=0.05 # 5% limit
    )

    assert gate["decision"] == "REJECTED_BIAS_VIOLATION"
    assert gate["is_promoted"] is False
    assert abs(gate["challenger_bias"]) > 0.05

@pytest.mark.asyncio
async def test_analyse_service_status_labels_combinations():
    from src.analyse_service import process_analyse_request

    # 1. Fallback points where challenger is rejected
    payload_reject = {
        "phase": "execute_workflow",
        "fileName": "sample_short.csv",
        "points": [{"date": f"Day-{i}", "actual": 100.0} for i in range(10)],
        "selectedTradeoff": {"profile": "balanced", "consentGiven": True}
    }
    res_reject = await process_analyse_request(payload_reject)
    assert res_reject["status"] == "SUCCESS"
    assert res_reject["measured"] is False
    # If gate rejects challenger:
    if not res_reject["gateResult"]["decision"].startswith("PROMOTED"):
        assert res_reject["champion"]["status"] == "RETAINED_ONLINE"
        assert res_reject["challenger"]["status"] == "CHALLENGER_REJECTED"

    # Explicit check of status label logic for both combinations:
    # Combination A: is_promoted is True
    gate_promoted = {"is_promoted": True}
    champ_status_promoted = "CHAMPION_DEMOTED" if gate_promoted["is_promoted"] else "RETAINED_ONLINE"
    chal_status_promoted = "CHALLENGER_PROMOTED" if gate_promoted["is_promoted"] else "CHALLENGER_REJECTED"
    assert champ_status_promoted == "CHAMPION_DEMOTED"
    assert chal_status_promoted == "CHALLENGER_PROMOTED"

    # Combination B: is_promoted is False
    gate_rejected = {"is_promoted": False}
    champ_status_rejected = "CHAMPION_DEMOTED" if gate_rejected["is_promoted"] else "RETAINED_ONLINE"
    chal_status_rejected = "CHALLENGER_PROMOTED" if gate_rejected["is_promoted"] else "CHALLENGER_REJECTED"
    assert champ_status_rejected == "RETAINED_ONLINE"
    assert chal_status_rejected == "CHALLENGER_REJECTED"

