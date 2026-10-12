"""
Quantitative Champion-vs-Challenger Model Promotion Evaluation Gates.
Implements WAPE improvement, Wilcoxon Signed-Rank non-parametric statistical hypothesis test,
and normalized forecast bias bounds.
"""

from typing import Dict, Any, Union
import numpy as np
from scipy import stats

def evaluate_promotion_gate(
    y_true: Union[np.ndarray, list],
    champ_preds: Union[np.ndarray, list],
    chal_preds: Union[np.ndarray, list],
    wape_improvement_threshold: float = 0.0,
    wilcoxon_alpha: float = 0.05,
    max_absolute_bias: float = 0.05
) -> Dict[str, Any]:
    """
    Evaluates whether a candidate/challenger model qualifies for promotion over the champion.

    Criteria for PROMOTION:
    1. WAPE Improvement: Candidate WAPE strictly lower than Champion WAPE (or beats improvement threshold).
    2. Wilcoxon Signed-Rank Test: Candidate absolute error significantly lower than Champion (p < wilcoxon_alpha).
    3. Normalized Bias Bound: Candidate abs(bias) <= max_absolute_bias.

    Returns:
        Dict with decision ('PROMOTED', 'REJECTED_WORSE_WAPE', 'REJECTED_NOT_SIGNIFICANT', 'REJECTED_BIAS_VIOLATION'),
        p-value, candidate WAPE, champion WAPE, candidate bias, champion bias, and reasons.
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    champ_arr = np.asarray(champ_preds, dtype=float)
    chal_arr = np.asarray(chal_preds, dtype=float)

    total_actual = float(np.sum(np.abs(y_true_arr)))
    if total_actual == 0:
        total_actual = 1.0

    champ_abs_errors = np.abs(y_true_arr - champ_arr)
    chal_abs_errors = np.abs(y_true_arr - chal_arr)

    champ_wape = float(np.sum(champ_abs_errors) / total_actual)
    chal_wape = float(np.sum(chal_abs_errors) / total_actual)

    champ_bias = float(np.sum(champ_arr - y_true_arr) / total_actual)
    chal_bias = float(np.sum(chal_arr - y_true_arr) / total_actual)

    wape_diff = champ_wape - chal_wape
    wape_improvement_pct = (wape_diff / max(0.001, champ_wape)) * 100.0

    # Paired Wilcoxon Signed-Rank Test on absolute errors
    diffs = champ_abs_errors - chal_abs_errors
    non_zero_diffs = diffs[diffs != 0]

    if len(non_zero_diffs) >= 10:
        try:
            # We test alternative='greater' (champ errors > chal errors, i.e., challenger error is smaller)
            res = stats.wilcoxon(champ_abs_errors, chal_abs_errors, alternative="greater")
            p_value = float(res.pvalue)
        except Exception:
            # Fallback two-sided or approximation
            try:
                res = stats.wilcoxon(diffs)
                p_value = float(res.pvalue)
            except Exception:
                p_value = 1.0
    elif len(non_zero_diffs) > 0:
        # Fewer than 10 non-zero pairs: test with wilcoxon or sign test
        try:
            res = stats.wilcoxon(diffs, alternative="greater")
            p_value = float(res.pvalue)
        except Exception:
            p_value = 0.5
    else:
        p_value = 1.0

    # Decision tree
    decision = "PROMOTED"
    reasons = []

    if chal_wape >= champ_wape or wape_improvement_pct < (wape_improvement_threshold * 100):
        decision = "REJECTED_WORSE_WAPE"
        reasons.append(f"Challenger WAPE ({chal_wape*100:.2f}%) did not sufficiently outperform Champion ({champ_wape*100:.2f}%).")
    elif abs(chal_bias) > max_absolute_bias:
        decision = "REJECTED_BIAS_VIOLATION"
        reasons.append(f"Challenger bias ({chal_bias*100:.2f}%) violated safety threshold (+/-{max_absolute_bias*100:.1f}%).")
    elif p_value >= wilcoxon_alpha:
        decision = "REJECTED_NOT_SIGNIFICANT"
        reasons.append(f"Performance improvement was not statistically significant (Wilcoxon p = {p_value:.4f} >= {wilcoxon_alpha}).")
    else:
        decision = "PROMOTED"
        reasons.append(f"Statistically significant WAPE improvement (+{wape_improvement_pct:.1f}%, p = {p_value:.4f} < {wilcoxon_alpha}) with compliant bias ({chal_bias*100:.2f}%).")

    return {
        "decision": decision,
        "is_promoted": decision == "PROMOTED",
        "wilcoxon_p_value": round(p_value, 5),
        "champion_wape": round(champ_wape, 4),
        "challenger_wape": round(chal_wape, 4),
        "wape_improvement_pct": round(wape_improvement_pct, 2),
        "champion_bias": round(champ_bias, 4),
        "challenger_bias": round(chal_bias, 4),
        "max_absolute_bias": max_absolute_bias,
        "reasons": reasons,
        "hypothesis": f"Challenger achieves superior accuracy with p = {p_value:.4f} (alpha = {wilcoxon_alpha})"
    }
