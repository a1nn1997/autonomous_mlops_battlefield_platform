import datetime
from typing import Dict, Any, Tuple
import pandas as pd
from src.config import settings
from src.metrics.evaluator import calculate_wape, calculate_bias, evaluate_forecast
from src.models.lightgbm_model import LightGBMForecaster
from src.models.registry import ModelRegistry
from src.drift.detector import DriftDetector
from src.drift.decay import RollingWAPEDecayMonitor

class RetrainingPipeline:
    """
    Automated Retraining Orchestrator:
    1. Monitors drift & decay
    2. Triggers retrain on alert
    3. Trains shadow candidate on updated dataset
    4. Evaluates Champion vs. Shadow candidate in shadow mode
    5. Promotes or Rejects candidate via quantitative gate
    """

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.detector = DriftDetector()
        self.decay_monitor = RollingWAPEDecayMonitor()

    def run_pipeline(
        self,
        baseline_df: pd.DataFrame,
        incoming_df: pd.DataFrame,
        eval_slice_days: int = 14
    ) -> Dict[str, Any]:
        active_version, champion_model = self.registry.get_champion()

        # Step 1: Detect Drift & WAPE decay
        champ_preds = champion_model.predict(incoming_df)
        drift_report = self.detector.analyze_drift(
            baseline_df=baseline_df,
            current_df=incoming_df,
            current_preds=champ_preds
        )

        champ_metrics = self.registry._load_manifest()["versions"][active_version]["metrics"]
        base_wape = champ_metrics.get("wape", 0.25)

        incoming_with_pred = incoming_df.copy()
        incoming_with_pred["y_pred"] = champ_preds
        decay_report = self.decay_monitor.check_decay(
            baseline_wape=base_wape,
            production_df=incoming_with_pred
        )

        trigger_fired = drift_report["drift_detected"] or decay_report["alert"]
        reasons = []
        if drift_report["drift_detected"]:
            reasons.append(f"Feature/Prediction drift detected (Max PSI: {drift_report['max_psi']})")
        if decay_report["alert"]:
            reasons.append(f"WAPE decay exceeded threshold ({decay_report['relative_decay']*100:.1f}% increase)")

        if not trigger_fired:
            return {
                "triggered": False,
                "reason": "System is stable; no retraining required.",
                "drift_report": drift_report,
                "decay_report": decay_report,
                "gate_decision": "NO_ACTION"
            }

        # Step 2: Prepare Training Data (incorporating fresh incoming data)
        combined_df = pd.concat([baseline_df, incoming_df], ignore_index=True)
        combined_df["date"] = pd.to_datetime(combined_df["date"])
        combined_df = combined_df.sort_values(by="date").drop_duplicates(subset=["store_id", "item_id", "date"])

        # Split into training and shadow holdout validation slice
        cutoff_date = combined_df["date"].max() - pd.Timedelta(days=eval_slice_days)
        train_data = combined_df[combined_df["date"] <= cutoff_date]
        val_data = combined_df[combined_df["date"] > cutoff_date]

        # Step 3: Train Shadow Candidate Model
        shadow_candidate = LightGBMForecaster()
        shadow_candidate.fit(train_data, val_df=val_data)

        # Step 4: Shadow Mode / A-B Validation Comparison
        val_y_true = val_data["sales"].values
        champ_val_preds = champion_model.predict(val_data)
        shadow_val_preds = shadow_candidate.predict(val_data)

        champ_val_eval = evaluate_forecast(val_y_true, champ_val_preds)
        shadow_val_eval = evaluate_forecast(val_y_true, shadow_val_preds)

        wape_improvement = (champ_val_eval["wape"] - shadow_val_eval["wape"]) / max(0.01, champ_val_eval["wape"])

        # Step 5: Promotion Gate with statistical significance and bias bounds
        from src.metrics.gates import evaluate_promotion_gate
        gate_res = evaluate_promotion_gate(
            y_true=val_y_true,
            champ_preds=champ_val_preds,
            chal_preds=shadow_val_preds,
            wape_improvement_threshold=0.0,
            wilcoxon_alpha=settings.drift.ks_significance_level,
            max_absolute_bias=0.05
        )

        timestamp_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        candidate_version = f"v_shadow_{timestamp_str}"
        promote = gate_res["is_promoted"]
        gate_decision = gate_res["decision"]

        self.registry.register(
            version=candidate_version,
            forecaster=shadow_candidate,
            metrics=shadow_val_eval,
            description=f"Auto-retrained candidate on drift alert ({', '.join(reasons)})",
            promote=promote
        )

        return {
            "triggered": True,
            "trigger_reasons": reasons,
            "drift_report": drift_report,
            "decay_report": decay_report,
            "shadow_comparison": {
                "champion_version": active_version,
                "champion_val_wape": champ_val_eval["wape"],
                "champion_val_bias": champ_val_eval["bias"],
                "candidate_version": candidate_version,
                "candidate_val_wape": shadow_val_eval["wape"],
                "candidate_val_bias": shadow_val_eval["bias"],
                "wape_improvement_pct": round(wape_improvement * 100, 2)
            },
            "gate_decision": gate_decision,
            "new_active_version": candidate_version if promote else active_version
        }
