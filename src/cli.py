import typer
import json
import uvicorn
from rich.console import Console
from rich.table import Table
from pathlib import Path

from src.config import settings, DATA_DIR, REGISTRY_DIR
from src.data.dataset import RetailDemandDataset
from src.data.features import FeaturePipeline
from src.data.split import TimeBasedSplitter
from src.metrics.evaluator import calculate_wape, calculate_bias, evaluate_forecast, evaluate_by_segment
from src.models.baselines import NaiveBaseline, SeasonalNaiveBaseline
from src.models.lightgbm_model import LightGBMForecaster
from src.models.comparator import ETSComparator
from src.models.time_series_cv import TimeSeriesCV
from src.models.registry import ModelRegistry
from src.drift.detector import DriftDetector
from src.drift.decay import RollingWAPEDecayMonitor
from src.drift.simulator import DriftSimulator
from src.drift.pipeline import RetrainingPipeline
from src.explainer.agent import GeminiIncidentExplainer
from src.explainer.benchmark import ExplainerBenchmark

app = typer.Typer(help="Forecast-to-Insight ML System CLI", add_completion=False)
console = Console()

@app.command()
def train(
    force_data: bool = typer.Option(False, "--force-data", help="Force regenerate dataset"),
    version: str = typer.Option("v1", "--version", help="Model version ID to register")
):
    """Generates data, fits LightGBM + ETS + Baselines, evaluates WAPE/Bias, and registers champion."""
    console.rule("[bold cyan]Forecast-to-Insight: Model Training & Baseline Evaluation[/bold cyan]")

    # 1. Data Ingestion & Features
    with console.status("Generating / loading retail demand dataset..."):
        ds = RetailDemandDataset()
        raw_df = ds.load_or_generate(force_generate=force_data)
        pipeline = FeaturePipeline()
        features_df = pipeline.fit_transform(raw_df)

    splitter = TimeBasedSplitter()
    train_df, val_df, test_df = splitter.split(features_df)
    console.print(f"[green]✓[/green] Dataset split: Train={len(train_df)} rows, Val={len(val_df)} rows, Test={len(test_df)} rows")

    # 2. Evaluate Baselines
    with console.status("Evaluating Naive & Seasonal-Naive baselines..."):
        y_test = test_df["sales"].values

        naive = NaiveBaseline()
        naive_preds = naive.predict(test_df)
        naive_eval = evaluate_forecast(y_test, naive_preds)

        s_naive = SeasonalNaiveBaseline()
        s_naive_preds = s_naive.predict(test_df)
        s_naive_eval = evaluate_forecast(y_test, s_naive_preds)

    # 3. Train Time-Series Comparator (ETS Holt-Winters)
    with console.status("Fitting ETS Holt-Winters comparator..."):
        ets = ETSComparator()
        ets.fit(train_df)
        ets_preds = ets.predict(test_df)
        ets_eval = evaluate_forecast(y_test, ets_preds)

    # 4. Train LightGBM Forecaster
    with console.status("Fitting LightGBM Regressor (L1 / WAPE aligned)..."):
        lgbm = LightGBMForecaster()
        lgbm.fit(train_df, val_df=val_df)
        lgbm_preds = lgbm.predict(test_df)
        lgbm_eval = evaluate_forecast(y_test, lgbm_preds)

    # Print Comparison Table
    table = Table(title="Test Set Performance: Baselines vs. Models")
    table.add_column("Model", style="bold")
    table.add_column("WAPE", justify="right")
    table.add_column("Bias", justify="right")
    table.add_column("MAE", justify="right")
    table.add_column("RMSE", justify="right")
    table.add_column("Status", justify="center")

    table.add_row("Naive (t-1)", f"{naive_eval['wape']:.2%}", f"{naive_eval['bias']:+.2%}", str(naive_eval['mae']), str(naive_eval['rmse']), "Baseline")
    table.add_row("Seasonal Naive (t-7)", f"{s_naive_eval['wape']:.2%}", f"{s_naive_eval['bias']:+.2%}", str(s_naive_eval['mae']), str(s_naive_eval['rmse']), "Baseline")
    table.add_row("ETS (Holt-Winters)", f"{ets_eval['wape']:.2%}", f"{ets_eval['bias']:+.2%}", str(ets_eval['mae']), str(ets_eval['rmse']), "Comparator")
    table.add_row("LightGBM (Proposed)", f"[bold green]{lgbm_eval['wape']:.2%}[/bold green]", f"{lgbm_eval['bias']:+.2%}", str(lgbm_eval['mae']), str(lgbm_eval['rmse']), "[bold green]Champion Candidate[/bold green]")
    console.print(table)

    # 5. Segment breakdown for LightGBM
    test_eval_df = test_df.copy()
    test_eval_df["y_pred"] = lgbm_preds
    seg_df = evaluate_by_segment(test_eval_df, segment_cols=["dept_id"])
    seg_table = Table(title="LightGBM Performance by Department Segment")
    seg_table.add_column("Department")
    seg_table.add_column("Count", justify="right")
    seg_table.add_column("WAPE", justify="right")
    seg_table.add_column("Bias", justify="right")
    for _, row in seg_df[seg_df["segment_dimension"] == "dept_id"].iterrows():
        seg_table.add_row(row["segment_value"], str(row["count"]), f"{row['wape']:.2%}", f"{row['bias']:+.2%}")
    console.print(seg_table)

    # 6. Register Model
    registry = ModelRegistry()
    meta = registry.register(
        version=version,
        forecaster=lgbm,
        metrics=lgbm_eval,
        description=f"Initial trained champion (Test WAPE: {lgbm_eval['wape']:.2%})",
        promote=True
    )
    console.print(f"[bold green]✓ Successfully registered {version} as CHAMPION in Model Registry.[/bold green]")

@app.command()
def cv(splits: int = 4, test_days: int = 14):
    """Runs expanding-window walk-forward Cross-Validation."""
    console.rule("[bold cyan]Time-Series Cross-Validation[/bold cyan]")
    ds = RetailDemandDataset()
    raw_df = ds.load_or_generate()
    pipeline = FeaturePipeline()
    features_df = pipeline.fit_transform(raw_df)

    cv_evaluator = TimeSeriesCV(n_splits=splits, test_days=test_days)
    results = cv_evaluator.evaluate(features_df, settings.model.lgbm_params)

    table = Table(title="Walk-Forward CV Fold Results")
    table.add_column("Fold")
    table.add_column("Train Days", justify="right")
    table.add_column("Test Days", justify="right")
    table.add_column("WAPE", justify="right")
    table.add_column("Bias", justify="right")

    for f in results["folds"]:
        table.add_row(str(f["fold"]), str(f["train_days"]), str(f["test_days"]), f"{f['wape']:.2%}", f"{f['bias']:+.2%}")
    console.print(table)
    console.print(f"[bold]Mean CV WAPE:[/bold] {results['mean_wape']:.2%} (±{results['std_wape']:.2%})")
    console.print(f"[bold]Mean CV Bias:[/bold] {results['mean_bias']:+.2%}")

@app.command()
def serve(
    host: str = settings.serving.host,
    port: int = settings.serving.port
):
    """Starts the production FastAPI forecasting service."""
    console.print(f"[bold cyan]Starting FastAPI serving on http://{host}:{port}[/bold cyan]")
    uvicorn.run("src.serving.app:app", host=host, port=port, reload=False)

@app.command()
def inject_drift(
    shift: str = typer.Option("price_shock", help="Shift type: price_shock, promo_surge, demand_drop, weekend_shift"),
    output_path: str = "data/processed/drift_slice.csv"
):
    """Injects synthetic distribution shift into data slice."""
    console.rule(f"[bold yellow]Injecting Drift: {shift}[/bold yellow]")
    ds = RetailDemandDataset()
    raw_df = ds.load_or_generate()
    shifted_df = DriftSimulator.inject_drift(raw_df, shift_type=shift, slice_fraction=0.4)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    shifted_df.to_csv(out, index=False)
    console.print(f"[green]✓ Drift injected slice saved to {output_path} ({len(shifted_df)} rows)[/green]")

@app.command()
def detect_drift(
    drift_slice: str = "data/processed/drift_slice.csv"
):
    """Evaluates PSI and KS tests between baseline and drift slice."""
    console.rule("[bold magenta]Distribution Drift Detection (PSI / KS)[/bold magenta]")
    ds = RetailDemandDataset()
    raw_df = ds.load_or_generate()
    pipeline = FeaturePipeline()
    base_df = pipeline.fit_transform(raw_df)
    
    slice_path = Path(drift_slice)
    if not slice_path.exists():
        console.print("[red]Drift slice not found. Injecting price_shock first...[/red]")
        base_slice = DriftSimulator.inject_drift(raw_df, "price_shock")
    else:
        import pandas as pd
        base_slice = pd.read_csv(slice_path)

    detector = DriftDetector()
    report = detector.analyze_drift(base_df, base_slice)

    table = Table(title="Covariate Drift Metrics")
    table.add_column("Feature")
    table.add_column("PSI", justify="right")
    table.add_column("KS p-value", justify="right")
    table.add_column("Base Mean", justify="right")
    table.add_column("Slice Mean", justify="right")
    table.add_column("Status", justify="center")

    for feat, data in report["features"].items():
        color = "green" if data["status"] == "STABLE" else ("yellow" if data["status"] == "WARNING" else "red")
        table.add_row(
            feat,
            str(data["psi"]),
            str(data["ks_p_value"]),
            str(data["baseline_mean"]),
            str(data["current_mean"]),
            f"[{color}]{data['status']}[/{color}]"
        )
    console.print(table)
    console.print(f"[bold]Max PSI:[/bold] {report['max_psi']} | [bold]Drift Alert Fired:[/bold] {report['drift_detected']}")

@app.command()
def retrain(
    drift_slice: str = "data/processed/drift_slice.csv"
):
    """Executes automated shadow retraining and promotion gate."""
    console.rule("[bold cyan]Automated Retraining & Shadow Evaluation Gate[/bold cyan]")
    registry = ModelRegistry()
    ds = RetailDemandDataset()
    raw_df = ds.load_or_generate()
    pipeline = FeaturePipeline()
    base_df = pipeline.fit_transform(raw_df)

    slice_path = Path(drift_slice)
    if not slice_path.exists():
        console.print("[yellow]Drift slice not found. Generating price_shock drift...[/yellow]")
        slice_df = DriftSimulator.inject_drift(raw_df, "price_shock")
    else:
        import pandas as pd
        slice_df = pd.read_csv(slice_path)

    pipe = RetrainingPipeline(registry=registry)
    result = pipe.run_pipeline(baseline_df=base_df, incoming_df=slice_df)

    if not result["triggered"]:
        console.print(f"[yellow]{result['reason']}[/yellow]")
        return

    comp = result["shadow_comparison"]
    table = Table(title="Shadow Mode Validation Comparison")
    table.add_column("Model")
    table.add_column("Version")
    table.add_column("Validation WAPE", justify="right")
    table.add_column("Validation Bias", justify="right")

    table.add_row("Champion (Active)", comp["champion_version"], f"{comp['champion_val_wape']:.2%}", f"{comp['champion_val_bias']:+.2%}")
    table.add_row("Shadow Candidate", comp["candidate_version"], f"[bold green]{comp['candidate_val_wape']:.2%}[/bold green]", f"{comp['candidate_val_bias']:+.2%}")
    console.print(table)

    gate = result["gate_decision"]
    color = "green" if gate == "PROMOTED" else "red"
    console.print(f"[bold]Gate Decision:[/bold] [{color}]{gate}[/{color}] (WAPE improvement: +{comp['wape_improvement_pct']}%)")
    console.print(f"[bold]Active Model Version Now:[/bold] {result['new_active_version']}")

@app.command()
def rollback():
    """Rolls back the active model to the previous champion."""
    console.rule("[bold red]Model Registry: Emergency Rollback[/bold red]")
    registry = ModelRegistry()
    try:
        new_active, prev_active = registry.rollback()
        console.print(f"[bold green]✓ Successfully rolled back active champion from {prev_active} to {new_active}.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Rollback error: {str(e)}[/bold red]")

@app.command()
def benchmark():
    """Runs 32-case Golden Dataset benchmark comparing Gemini vs OpenAI."""
    console.rule("[bold cyan]GenAI Explainer: Golden Set Benchmark (Gemini vs OpenAI)[/bold cyan]")
    bench = ExplainerBenchmark()
    summary = bench.run_benchmark()

    table = Table(title="Explainer Performance Benchmark (32 Golden Incident Cases)")
    table.add_column("Provider", style="bold")
    table.add_column("Diagnostic Accuracy", justify="right")
    table.add_column("Metric Citation Adherence", justify="right")
    table.add_column("p50 Latency (ms)", justify="right")
    table.add_column("p95 Latency (ms)", justify="right")
    table.add_column("Cost / 1K Reports", justify="right")

    for row in summary["summary_table"]:
        table.add_row(
            row["provider"],
            row["diagnostic_accuracy"],
            row["citation_adherence"],
            str(row["latency_p50_ms"]),
            str(row["latency_p95_ms"]),
            row["cost_per_1k_reports_usd"]
        )
    console.print(table)

@app.command()
def demo():
    """Executes the full end-to-end Forecast-to-Insight demo."""
    from src.demo import run_full_demo
    run_full_demo()

if __name__ == "__main__":
    app()
