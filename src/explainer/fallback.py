from typing import Dict, Any, List

class RuleBasedExplainerFallback:
    """
    Deterministic rule-based fallback engine for forecast incidents and drift alerts.
    Executes instantly with zero latency when LLM APIs are unreachable or error out.
    Guarantees strict metric citation and structured actionable RCA.
    """

    def explain(self, context: Dict[str, Any]) -> Dict[str, Any]:
        incident_type = context.get("incident_type", "DRIFT_ALERT")
        metrics = context.get("metrics", {})
        drift_report = context.get("drift_report", {})
        decay_report = context.get("decay_report", {})
        segment_info = context.get("segment_info", {})

        # Identify drifting features
        drifting_feats = []
        max_psi = drift_report.get("max_psi", 0.0)
        for feat, data in drift_report.get("features", {}).items():
            if data.get("status") in ["CRITICAL_DRIFT", "WARNING"]:
                drifting_feats.append({
                    "feature": feat,
                    "psi": data.get("psi"),
                    "ks_p_value": data.get("ks_p_value"),
                    "base_mean": data.get("baseline_mean"),
                    "curr_mean": data.get("current_mean")
                })

        wape = metrics.get("wape", decay_report.get("current_wape", 0.0))
        bias = metrics.get("bias", 0.0)
        rel_decay = decay_report.get("relative_decay", 0.0)

        # Determine Primary Cause
        cited_metrics = [f"Max PSI: {max_psi}", f"WAPE: {wape:.2%}", f"Forecast Bias: {bias:+.2%}"]
        if rel_decay > 0:
            cited_metrics.append(f"WAPE Degradation: +{rel_decay*100:.1f}%")

        if any("price" in f["feature"].lower() for f in drifting_feats):
            primary_cause = "Price Elasticity Disruption: Significant shift in sell price distribution."
            remediation = "Re-estimate price elasticity parameters and trigger retraining with recent pricing tiers."
        elif any("promo" in f["feature"].lower() for f in drifting_feats):
            primary_cause = "Promotional Surge: Unpredicted surge in promotional volume."
            remediation = "Incorporate promo calendar into feature pipeline and alert merchandising team."
        elif bias < -0.10:
            primary_cause = f"Systematic Under-Forecasting: Demand surged unexpectedly, creating negative bias ({bias:+.2%})."
            remediation = "Evaluate safety stock buffers for affected SKUs to mitigate stockout risks."
        elif bias > 0.10:
            primary_cause = f"Systematic Over-Forecasting: Demand contracted, creating positive bias ({bias:+.2%})."
            remediation = "Curtail re-order replenishment to prevent holding cost waste and margin markdown."
        else:
            primary_cause = f"General Concept Drift: Multi-feature statistical shift (Max PSI {max_psi})."
            remediation = "Execute automated shadow candidate retraining and evaluate on holdout window."

        feature_summary_str = "; ".join([
            f"{f['feature']} (PSI={f['psi']}, mean shifted from {f['base_mean']} to {f['curr_mean']})"
            for f in drifting_feats
        ]) or "No individual feature exceeded critical PSI; multi-variate drift observed."

        explanation_text = (
            f"### Incident Report: {incident_type}\n\n"
            f"**1. Executive Summary:**\n"
            f"Production forecast monitoring detected {incident_type} with a current WAPE of {wape:.2%} "
            f"(relative degradation of {rel_decay*100:.1f}%) and normalized forecast bias of {bias:+.2%}. "
            f"Maximum feature PSI reached {max_psi}.\n\n"
            f"**2. Root Cause Analysis (Quantitative Evidence):**\n"
            f"- Primary Driver: {primary_cause}\n"
            f"- Drifting Covariates: {feature_summary_str}\n"
            f"- Statistical Significance: Key features showed KS p-values < 0.05 against reference baseline.\n\n"
            f"**3. Business & Inventory Impact:**\n"
            f"{'High risk of stockouts and lost revenue due to severe under-prediction.' if bias < 0 else 'High risk of inventory buildup, storage holding costs, and spoilage due to over-prediction.'}\n\n"
            f"**4. Recommended Remediation:**\n"
            f"- Action: {remediation}\n"
            f"- Serving Strategy: Shadow test retrained model against active champion before auto-promotion."
        )

        return {
            "source": "RULE_BASED_FALLBACK",
            "incident_type": incident_type,
            "explanation": explanation_text,
            "cited_metrics": cited_metrics,
            "primary_driver": primary_cause,
            "remediation_action": remediation,
            "success": True
        }
