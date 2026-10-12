---
name: champion-challenger-ml
description: Autonomous Champion vs Challenger machine learning workflow for time-series demand forecasting with tradeoff profiling, shadow evaluation gate, online serving promotion, and cloud orchestration on Google Cloud Platform (BigQuery ML, Vertex AI, Cloud Run, Kubernetes).
---

# Champion vs Challenger ML Autonomous Workflow Skill

This skill defines the autonomous end-to-end operational protocol for evaluating, selecting, and deploying Champion and Challenger forecasting models on custom customer demand datasets in both online serving mode and cloud orchestration environments.

---

## 1. Architectural Overview

```
                                [ Ingested CSV / Live Stream ]
                                              │
                                              ▼
                                 [ Automated Profiler & EDA ]
                       (Sparsity, CV Volatility, Seasonality Index)
                                              │
                                              ▼
                             [ Tradeoff Matrix & Consent Gate ]
                        (Latency SLA vs. Precision vs. Cloud Cost)
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
         [ Active Champion Candidate ]                   [ Shadow Challenger Candidate ]
             LightGBM Forecaster                             ETS Holt-Winters / Ensemble
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              ▼
                             [ Automated Promotion Gate ]
                   • WAPE Lift >= 10%
                   • Bias within [-0.03, +0.03]
                   • Wilcoxon p-value < 0.05
                   • Latency SLA < 15ms
                                              │
                                              ▼
                         [ Online Serving Atomic Swap ]
                       Zero-Downtime Pointer Promotion (<15ms)
                                              │
                                              ▼
                         [ Cloud Production Manifests ]
                     Vertex AI • Cloud Run • Kubernetes HPA
```

---

## 2. Tradeoff Profiling & User Consent Protocol

Before autonomous model execution, the agent must evaluate the dataset characteristics and obtain explicit **User Consent** across three operational tradeoff profiles:

| Profile | Target Latency (p99) | Target WAPE | Throughput (RPS) | Memory Footprint | Recommended Use Case |
|---|---|---|---|---|---|
| **⚡ Low-Latency Online** | `< 5 ms` | `7.0% - 8.5%` | `> 1,200 RPS` | `< 128 MB` | High-volume retail checkout, edge POS cash registers |
| **🎯 High-Precision Ensemble** | `< 35 ms` | `< 5.5%` | `~ 150 RPS` | `~ 512 MB` | High-value supply chain replenishment, weekly PO purchasing |
| **⚖️ Balanced Production Tier** | `< 10 ms` | `5.5% - 6.5%` | `~ 350 RPS` | `~ 256 MB` | Default omni-channel e-commerce demand forecasting |

### Required Consent Parameters
- `consentGiven`: Boolean confirming user reviewed and accepted model resource/accuracy tradeoffs.
- `selectedProfile`: `"latency" | "accuracy" | "balanced" | "custom"`.
- `rollbackSafetyNet`: Automatic reversion to previous champion if live drift $\text{PSI} > 0.20$ or error rate exceeds $2\%$.

---

## 3. Automated Champion-Challenger Promotion Gate

A Challenger is promoted to Champion **only** when all four gate conditions evaluate to true:

$$\text{Gate Passed} \iff \begin{cases}
\text{WAPE}_{\text{Challenger}} < \text{WAPE}_{\text{Champion}} \times (1 - \delta_{\text{min}}) & (\delta_{\text{min}} = 0.05) \\
|\text{Bias}_{\text{Challenger}}| \le 0.03 & (\pm 3\%\text{ volume bias bound}) \\
p_{\text{value}} < 0.05 & (\text{Wilcoxon signed-rank test}) \\
t_{\text{p99}} \le \text{SLA}_{\text{max}} & (\text{Latency bound})
\end{cases}$$

If any condition fails, the Challenger remains in shadow monitoring mode, and a diagnostic RCA is emitted to the Sentinel Copilot.

---

## 4. Online Serving Mode Integration

When deployed in **Online Mode**:
1. **Atomic Pointer Switch**:
   The registry updates the active symlink `/models/registry/champion` to the newly promoted version ID within $< 15\text{ms}$.
2. **FastAPI Zero-Downtime Sync**:
   The serving container reloads model weights in memory without dropping in-flight HTTP connections.
3. **Fail-Safe Circuit Breaker**:
   If inference takes longer than $2.0\text{s}$, the serving gateway falls back to a deterministic **Seasonal Naive** baseline forecast:
   $$\hat{y}_{t} = y_{t - 7}$$

---

## 5. Google Cloud Orchestration Manifests

### 5.1 Vertex AI Training Pipeline (`pipeline.py`)

```python
from google.cloud import aiplatform
from kfp.v2 import dsl

@dsl.pipeline(
    name="champion-challenger-demand-forecast",
    description="Automated time-series champion vs challenger evaluation pipeline."
)
def forecast_pipeline(
    dataset_gcs_uri: str,
    target_wape_threshold: float = 0.10,
    tradeoff_profile: str = "balanced"
):
    # 1. Feature Engineering Step
    feat_step = dsl.ContainerOp(
        name="feature-engineering",
        image="gcr.io/mlops-forecasting/feature-prep:latest",
        arguments=["--input", dataset_gcs_uri, "--profile", tradeoff_profile]
    )

    # 2. Train Champion Candidate (LightGBM)
    train_champ = dsl.ContainerOp(
        name="train-champion-candidate",
        image="gcr.io/mlops-forecasting/lightgbm-train:latest",
        arguments=["--features", feat_step.output]
    )

    # 3. Train Shadow Challenger (ETS Holt-Winters)
    train_challenger = dsl.ContainerOp(
        name="train-shadow-challenger",
        image="gcr.io/mlops-forecasting/ets-train:latest",
        arguments=["--features", feat_step.output]
    )

    # 4. Statistical Promotion Gate
    gate_step = dsl.ContainerOp(
        name="champion-gate-evaluator",
        image="gcr.io/mlops-forecasting/promotion-gate:latest",
        arguments=[
            "--champ-model", train_champ.output,
            "--challenger-model", train_challenger.output,
            "--wape-threshold", target_wape_threshold
        ]
    )
```

### 5.2 BigQuery ML Baseline Model SQL

```sql
-- Automated baseline model generation in BigQuery ML
CREATE OR REPLACE MODEL `demand_forecast.arima_plus_challenger`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'actual_sales',
  time_series_id_col = 'sku_id',
  holiday_region = 'US',
  auto_arima = TRUE,
  data_frequency = 'DAILY'
) AS
SELECT
  PARSE_DATE('%Y-%m-%d', date) AS date,
  sku_id,
  actual_sales
FROM
  `demand_forecast.raw_demand_feed`
WHERE
  date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);
```

### 5.3 Kubernetes Online Deployment with HPA (`k8s-champion.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forecast-champion-serving
  labels:
    app: forecast-champion
    tier: online-serving
spec:
  replicas: 3
  selector:
    matchLabels:
      app: forecast-champion
  template:
    metadata:
      labels:
        app: forecast-champion
    spec:
      containers:
      - name: forecaster
        image: gcr.io/mlops-forecasting/serving:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: SERVING_MODE
          value: "online-champion"
        - name: TIMEOUT_SECONDS
          value: "2.0"
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "1000m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: forecast-champion-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: forecast-champion-serving
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```
