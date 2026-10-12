import os
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REGISTRY_DIR = MODELS_DIR / "registry"

class DataConfig(BaseModel):
    n_items: int = 10
    n_stores: int = 4
    start_date: str = "2023-01-01"
    end_date: str = "2024-06-30"
    train_end_date: str = "2024-03-31"
    val_end_date: str = "2024-05-15"
    test_end_date: str = "2024-06-30"
    target_col: str = "sales"
    id_cols: List[str] = ["store_id", "item_id", "dept_id"]
    date_col: str = "date"

class FeatureConfig(BaseModel):
    lags: List[int] = [1, 7, 14, 28]
    rolling_windows: List[int] = [7, 14, 28]
    categorical_cols: List[str] = ["store_id", "item_id", "dept_id", "day_of_week", "month"]
    numeric_features: List[str] = [
        "sell_price", "is_promo", "is_weekend",
        "lag_1", "lag_7", "lag_14", "lag_28",
        "rolling_mean_7", "rolling_std_7",
        "rolling_mean_14", "rolling_std_14",
        "rolling_mean_28", "rolling_std_28",
        "price_ratio_28"
    ]

class ModelConfig(BaseModel):
    lgbm_params: Dict[str, Any] = {
        "objective": "regression_l1",  # L1 aligns directly with WAPE/MAE optimization
        "metric": "mae",
        "boosting_type": "gbdt",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "n_estimators": 150,
        "min_child_samples": 20,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "verbose": -1
    }
    cv_n_splits: int = 4
    cv_test_size_days: int = 14

class ServingConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    timeout_seconds: float = 2.0
    max_retries: int = 3
    retry_backoff: float = 0.2

class DriftConfig(BaseModel):
    psi_warning_threshold: float = 0.10
    psi_critical_threshold: float = 0.20
    ks_significance_level: float = 0.05
    wape_decay_threshold: float = 0.15  # 15% relative increase in WAPE triggers retraining alert
    window_days: int = 14

class Settings(BaseModel):
    data: DataConfig = Field(default_factory=DataConfig)
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    serving: ServingConfig = Field(default_factory=ServingConfig)
    drift: DriftConfig = Field(default_factory=DriftConfig)

settings = Settings()
