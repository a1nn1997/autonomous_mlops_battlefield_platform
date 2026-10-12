# 🏛️ Low-Level Design (LLD) & Software Architecture Specification

**System:** Forecast-to-Insight Autonomous Demand Forecasting & Agentic MLOps Platform  
**Architecture Paradigm:** Object-Oriented Domain-Driven Design (DDD), SOLID Principles, Cloud-Native Mesh  
**Author:** Staff ML Systems Architect & Forward Deployed Engineering Lead  
**Status:** Approved & Implemented in Production  

---

## 1. 📐 Architectural Philosophy & SOLID Principles Mapping

The core design of the Forecast-to-Insight platform adheres strictly to the five **SOLID** design principles, ensuring production resilience, zero temporal leakage, modular testability, and enterprise-grade extensibility:

```mermaid
graph TD
    subgraph SOLID["SOLID Principles in Forecast-to-Insight"]
        SRP["<b>S</b> - Single Responsibility<br/>Dedicated micro-components for features, metrics, drift, serving & agentic analysis"]
        OCP["<b>O</b> - Open/Closed<br/>Pluggable Forecasters, Metrics & LLM Providers via polymorphic factories"]
        LSP["<b>L</b> - Liskov Substitution<br/>Any IForecaster replaces any baseline without side-effects or interface mutations"]
        ISP["<b>I</b> - Interface Segregation<br/>Discrete thin interfaces: IForecaster, ITrainable, IVersionable, IModelRegistry"]
        DIP["<b>D</b> - Dependency Inversion<br/>High-level pipelines depend on abstractions, never concrete database or cloud drivers"]
    end
```

### Concrete Code Mapping Matrix

| Principle | Architectural Mechanism | Implementation in Codebase |
|---|---|---|
| **S** (Single Responsibility) | Dedicated modules with single reason to change | [src/data/features.py](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/src/data/features.py) handles feature engineering; [src/drift/psi.py](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/src/drift/psi.py) handles population stability; [src/metrics/evaluator.py](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/src/metrics/evaluator.py) calculates WAPE/Bias/MAE; [src/models/registry.py](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/src/models/registry.py) manages artifact lifecycle. |
| **O** (Open/Closed) | Strategy & Factory patterns | Adding a new forecasting architecture (e.g. Prophet, DeepAR) or new LLM vendor requires implementing `IForecaster` or `LLMProvider` without altering serving middleware or UI routes. |
| **L** (Liskov Substitution) | Strict interface conformance | [LightGBMForecaster](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/src/models/lightgbm_model.py), [ETSHoltWinters](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/src/models/baselines.py), and [SeasonalNaiveForecaster](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/src/models/baselines.py) all honor `predict(df: pd.DataFrame) -> np.ndarray`. |
| **I** (Interface Segregation) | Thin interface contracts | Separation between `IForecaster` (pure prediction contract), `ITrainable` (offline training contract), `IVersionable` (serialization contract), and `IModelRegistry` (metadata repository). |
| **D** (Dependency Inversion) | Inversion of Control & Abstraction | [src/serving/app.py](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/src/serving/app.py) and [ui/app/api/battle/route.ts](file:///home/ann/Desktop/desktop/autonomous_mlops_battlefield_platform/ui/app/api/battle/route.ts) depend on abstract forecaster interfaces, not raw disk paths or hardcoded models. |

---

## 2. 🧩 Structural UML Class Diagram

```mermaid
classDiagram
    class IForecaster {
        <<interface>>
        +predict(df: DataFrame) ndarray*
    }

    class ITrainable {
        <<interface>>
        +fit(train_df: DataFrame, val_df: DataFrame) ITrainable*
    }

    class IVersionable {
        <<interface>>
        +save(model_dir: Path) void*
        +load(model_dir: Path) IVersionable*
        +get_feature_importance() Dict~str, float~*
    }

    class LightGBMForecaster {
        -params: Dict
        -model: Booster
        -feature_names: List~str~
        +fit(train_df, val_df) LightGBMForecaster
        +predict(df) ndarray
        +save(model_dir) void
        +load(model_dir) LightGBMForecaster
    }

    class ETSHoltWinters {
        -trend: str
        -seasonal: str
        -seasonal_periods: int
        -fitted_models: Dict
        +fit(train_df, val_df) ETSHoltWinters
        +predict(df) ndarray
    }

    class SeasonalNaiveForecaster {
        -lag: int
        -history: Dict
        +fit(train_df, val_df) SeasonalNaiveForecaster
        +predict(df) ndarray
    }

    class IModelRegistry {
        <<interface>>
        +register(version_id, model, metrics, promote) void*
        +get_champion() Tuple~str, IForecaster~*
        +rollback() Tuple~str, str~*
    }

    class ModelRegistry {
        -registry_dir: Path
        -manifest_path: Path
        +register(version_id, model, metrics, promote) void
        +get_champion() Tuple~str, IForecaster~
        +rollback() Tuple~str, str~
    }

    class TimeoutMiddleware {
        -timeout_seconds: float
        -fallback_forecaster: SeasonalNaiveForecaster
        +dispatch(request, call_next) Response
    }

    class MultiVendorLLMGateway {
        -provider: str
        -model: str
        +generate_rca(psi_report, drift_metrics) GatewayResponse
        +evaluate_golden_cases() BenchmarkSummary
    }

    class DeepAgenticLoopEngine {
        +profile_dataset(points) ProfilingResult
        +generate_plan() ExecutionPlan
        +enforce_consent_gate(profile, consent_given) Boolean
        +execute_champion_challenger(data, profile) TournamentResult
    }

    IForecaster <|.. LightGBMForecaster
    ITrainable <|.. LightGBMForecaster
    IVersionable <|.. LightGBMForecaster

    IForecaster <|.. ETSHoltWinters
    ITrainable <|.. ETSHoltWinters

    IForecaster <|.. SeasonalNaiveForecaster
    ITrainable <|.. SeasonalNaiveForecaster

    IModelRegistry <|.. ModelRegistry
    ModelRegistry --> IForecaster : stores & loads
    TimeoutMiddleware --> IForecaster : wraps champion
    TimeoutMiddleware --> SeasonalNaiveForecaster : circuit breaker fallback
    DeepAgenticLoopEngine --> IForecaster : evaluates Champion/Challenger
```

---

## 3. ⏱️ Sequence Diagrams for Production Flows

### 3.1 Online Prediction Flow with Circuit-Breaker SLA

```mermaid
sequenceDiagram
    autonumber
    actor Client as Production ERP / Store POS
    participant Proxy as Reverse Proxy / Ingress
    participant Middleware as TimeoutMiddleware (< 2.0s SLA)
    participant Champion as Active Champion (LightGBM)
    participant Fallback as Seasonal Naive Fallback

    Client->>Proxy: POST /predict (Demand Features)
    Proxy->>Middleware: Forward Request
    
    alt Inference within SLA (< 15ms)
        Middleware->>Champion: predict(features)
        Champion-->>Middleware: Output predictions (p50: 7.05ms)
        Middleware-->>Proxy: 200 OK + Forecast Payload
        Proxy-->>Client: Return Predictions
    else Timeout Exceeded (> 2.0s SLA)
        Middleware->>Champion: Request Timed Out (SIGALRM / Cancel)
        Middleware->>Fallback: Trigger Fallback predict(t-7 lag)
        Fallback-->>Middleware: Deterministic Baseline Predictions (0.2ms)
        Middleware-->>Proxy: 200 OK (X-Circuit-Breaker: Triggered)
        Proxy-->>Client: Safe Baseline Predictions (100% Availability)
    end
```

### 3.2 Continuous Drift Detection & Shadow Promotion Gate

```mermaid
sequenceDiagram
    autonumber
    participant Stream as Production Prediction Stream
    participant Monitor as Drift Telemetry Mesh
    participant Gate as Wilcoxon Promotion Gate
    participant Registry as ModelRegistry
    actor Copilot as Sentinel Agent Copilot

    Stream->>Monitor: Ingest daily predictions & ground truth actuals
    Monitor->>Monitor: Calculate PSI across 10 deciles & Rolling WAPE
    
    alt Critical Drift Detected (PSI >= 0.20 or Decay >= 15%)
        Monitor->>Monitor: Trigger automated shadow candidate training
        Monitor->>Gate: Evaluate Shadow Candidate vs. Active Champion
        Gate->>Gate: Check Wilcoxon p-value (< 0.05) & Bias bounds (<= 3.0%)
        
        alt Gate Passed (Candidate Superior)
            Gate->>Registry: Atomic pointer swap to new candidate (v2)
            Registry-->>Copilot: Emit PROMOTED event (< 15ms zero-downtime)
            Copilot->>Copilot: Log RCA & Autonomous Action in Chat
        else Gate Failed (Candidate Inferior)
            Gate-->>Copilot: Reject candidate & emit Root Cause Diagnosis
        end
    end
```

### 3.3 Deep Agentic Loop, Tradeoff Consent & Cloud Skill Orchestration

```mermaid
sequenceDiagram
    autonumber
    actor User as Forward Deployed Engineer / Customer
    participant UI as Next.js High-Density UI
    participant AgentAPI as Deep Agentic Loop Engine (/api/analyse)
    participant SkillRepo as Cloud Skill Repository (.agents/skills/)
    participant Serving as Online Serving Engine

    User->>UI: Upload Custom Demand CSV
    UI->>UI: Activate '⚡ LIVE' Mode & Render Raw Tabular Inspector
    User->>UI: Click '⚡ Analyse'
    UI->>AgentAPI: POST /api/analyse (phase: "profile")
    AgentAPI-->>UI: Return 5-Step Plan, Volatility CV, Sparsity & Tradeoff Profiles
    
    UI->>User: Display Tradeoff Matrix (Latency vs WAPE vs Cost)
    User->>UI: Select '⚖️ Balanced Production Tier' & Check Consent Box
    User->>UI: Click '🚀 Execute Autonomous Workflow'
    
    UI->>AgentAPI: POST /api/analyse (phase: "execute_workflow", consentGiven: true)
    AgentAPI->>AgentAPI: Run Champion (LGBM) vs Challenger (ETS) Tournament
    AgentAPI->>AgentAPI: Evaluate Wilcoxon p=0.0038 & 95% Confidence Forecast
    AgentAPI->>SkillRepo: Prepare champion-challenger-ml/SKILL.md
    AgentAPI-->>UI: Return Champion Promoted, Cloud Manifests & Optimal Horizon
    
    User->>UI: Click 'Activate in Online Serving Mode'
    UI->>Serving: Hot-reload active champion weights (< 15ms)
    Serving-->>UI: Confirm Zero-Downtime Serving Swapped
```

---

## 4. 🧠 Applied AI / Machine Learning Engineering Standards

1. **Strict Temporal Partitioning**:
   - Time-series cross-validation uses an **expanding window** (walk-forward split). No future information is ever leaked into past feature windows (`target_lag_1` is strictly calculated from $t-1$).
2. **Harmonic Day-of-Week Encoding**:
   - Day of week is represented as cyclical Fourier sine/cosine embeddings:
     $$\sin\left(\frac{2\pi \cdot \text{day}}{7}\right), \quad \cos\left(\frac{2\pi \cdot \text{day}}{7}\right)$$
   - Prevents artificial boundary cliffs between Sunday ($6$) and Monday ($0$).
3. **Thread-Safe Atomic Pointer Swapping**:
   - Model versions are saved in isolated directories `/models/registry/v1`, `/models/registry/v2`.
   - The active champion is exposed through a filesystem symbolic link `/models/registry/champion`.
   - Swapping models invokes an atomic POSIX `rename()` call on a temporary symlink, guaranteeing that no reader ever observes a broken or half-written pointer.
