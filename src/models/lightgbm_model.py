"""
LightGBM forecaster implementing IForecaster, ITrainable, and IVersionable interfaces.
Follows SOLID Principles:
- Single Responsibility: Gradient boosted tree fitting with L1 loss for demand forecasting.
- Open/Closed: Registered dynamically in ForecasterFactory.
- Liskov Substitution: Satisfies predict(), fit(), and save()/load() contracts.
- Interface Segregation: Segregates inference, training, and persistence interfaces.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import lightgbm as lgb
import numpy as np
import pandas as pd
from src.config import settings
from src.models.base import IForecaster, ITrainable, IVersionable, ForecasterFactory

class LightGBMForecaster(IForecaster, ITrainable, IVersionable):
    """
    LightGBM regressor tailored for retail demand forecasting.
    Optimizes L1 loss (MAE), directly aligning with WAPE minimization.
    Supports categorical features (store_id, item_id, dept_id).
    """

    def __init__(
        self,
        params: Optional[Dict[str, Any]] = None,
        feature_cols: Optional[List[str]] = None,
        categorical_cols: Optional[List[str]] = None,
        target_col: str = "sales"
    ):
        self.params = params or settings.model.lgbm_params.copy()
        self.feature_cols = feature_cols
        self.categorical_cols = categorical_cols or ["store_id", "item_id", "dept_id"]
        self.target_col = target_col
        self.model: Optional[lgb.Booster] = None
        self.trained_features: List[str] = []

    def _prepare_matrix(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[np.ndarray]]:
        df = df.copy()
        if self.feature_cols:
            features = [c for c in self.feature_cols if c in df.columns]
        else:
            exclude = [self.target_col, "date", "y_pred"]
            features = [c for c in df.columns if c not in exclude]

        X = df[features].copy()
        for cat in self.categorical_cols:
            if cat in X.columns:
                X[cat] = X[cat].astype("category")

        y = df[self.target_col].values if self.target_col in df.columns else None
        return X, y

    def fit(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None,
        early_stopping_rounds: int = 20,
        **kwargs: Any
    ) -> "LightGBMForecaster":
        X_train, y_train = self._prepare_matrix(train_df)
        self.trained_features = list(X_train.columns)

        cats = [c for c in self.categorical_cols if c in self.trained_features]
        train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=cats, free_raw_data=False)

        valid_sets = [train_data]
        valid_names = ["train"]

        callbacks = []
        if val_df is not None and len(val_df) > 0:
            X_val, y_val = self._prepare_matrix(val_df)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data, categorical_feature=cats, free_raw_data=False)
            valid_sets.append(val_data)
            valid_names.append("valid")
            callbacks.append(lgb.early_stopping(stopping_rounds=early_stopping_rounds, verbose=False))

        callbacks.append(lgb.log_evaluation(period=0))

        n_estimators = self.params.pop("n_estimators", 150)
        self.model = lgb.train(
            self.params,
            train_data,
            num_boost_round=n_estimators,
            valid_sets=valid_sets,
            valid_names=valid_names,
            callbacks=callbacks
        )
        self.params["n_estimators"] = n_estimators
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model is not fitted yet.")

        df = df.copy()
        # Ensure all expected features are present; populate defaults if omitted
        for feat in self.trained_features:
            if feat not in df.columns:
                df[feat] = 0

        X = df[self.trained_features].copy()
        for cat in self.categorical_cols:
            if cat in X.columns:
                X[cat] = X[cat].astype("category")

        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

    def get_feature_importance(self) -> Dict[str, float]:
        if self.model is None:
            return {}
        imp = self.model.feature_importance(importance_type="gain")
        total = np.sum(imp) if np.sum(imp) > 0 else 1.0
        return {feat: float(score / total) for feat, score in zip(self.trained_features, imp)}

    def save(self, model_dir: Path) -> None:
        model_dir.mkdir(parents=True, exist_ok=True)
        if self.model is not None:
            self.model.save_model(str(model_dir / "model.txt"))
        metadata = {
            "feature_cols": self.trained_features,
            "categorical_cols": self.categorical_cols,
            "target_col": self.target_col,
            "params": self.params
        }
        with open(model_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def load(cls, model_dir: Path) -> "LightGBMForecaster":
        with open(model_dir / "metadata.json", "r") as f:
            meta = json.load(f)
        forecaster = cls(
            params=meta["params"],
            feature_cols=meta["feature_cols"],
            categorical_cols=meta["categorical_cols"],
            target_col=meta["target_col"]
        )
        forecaster.model = lgb.Booster(model_file=str(model_dir / "model.txt"))
        forecaster.trained_features = meta["feature_cols"]
        return forecaster

# Register LightGBM in ForecasterFactory
ForecasterFactory.register_algorithm("lightgbm", LightGBMForecaster)
ForecasterFactory.register_algorithm("lgbm", LightGBMForecaster)
